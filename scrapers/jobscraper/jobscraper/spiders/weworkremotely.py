# scrapers/jobscraper/spiders/weworkremotely.py
import scrapy
import re
import json
from urllib.parse import urljoin
from datetime import datetime
from django.utils import timezone
from jobscraper.items import JobItem


class WeWorkRemotelySpider(scrapy.Spider):
    name = 'weworkremotely'
    allowed_domains = ['weworkremotely.com']
    start_urls = [
        'https://weworkremotely.com/categories/remote-programming-jobs',
        'https://weworkremotely.com/categories/remote-devops-sysadmin-jobs',
        'https://weworkremotely.com/categories/remote-design-jobs',
        'https://weworkremotely.com/categories/remote-marketing-jobs',
    ]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1,
    }
    
    def parse(self, response):
        """Parse job listing pages"""
        # Extract job links from the category page
        job_links = response.css('li.feature a::attr(href)').getall()
        
        for link in job_links:
            if link and '/remote-jobs/' in link:
                job_url = urljoin(response.url, link)
                yield response.follow(
                    job_url, 
                    self.parse_job,
                    meta={'category_url': response.url}
                )
        
        # Follow pagination if available
        next_page = response.css('a.next_page::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)
    
    def parse_job(self, response):
        """Parse individual job pages"""
        try:
            # Extract job information
            item = JobItem()
            
            # Basic job info
            item['title'] = self._extract_title(response)
            item['company_name'] = self._extract_company(response)
            item['external_id'] = self._extract_job_id(response.url)
            item['url'] = response.url
            item['source_name'] = 'WeWorkRemotely'
            
            # Job details
            item['raw_description'] = self._extract_description(response)
            item['raw_location'] = self._extract_location(response)
            item['raw_salary'] = self._extract_salary(response)
            
            # Employment details
            item['job_type'] = self._determine_job_type(response)
            item['tags'] = self._extract_tags(response)
            item['skills_required'] = self._extract_skills(response)
            
            # Posted date
            item['posted_date'] = self._extract_posted_date(response)
            
            self.logger.info(f"Scraped job: {item.get('title')} at {item.get('company_name')}")
            yield item
            
        except Exception as e:
            self.logger.error(f"Error parsing job from {response.url}: {str(e)}")
    
    def _extract_title(self, response):
        """Extract job title with JSON-LD, meta tag, and DOM fallbacks"""
        # Try JSON-LD first
        data = self._extract_from_json_ld(response)
        if data.get('title'):
            return data['title']

        # Direct selectors first
        title_selectors = [
            'h1.page-title::text',
            '.listing-header h1::text',
            '.listing-header h2::text',
            'h1::text',
            '.listing-header-container h1::text',
            '.listing-header-container h2::text',
            '.listing-header-content h1::text',
            '.listing-header-content h2::text',
        ]
        for sel in title_selectors:
            value = response.css(sel).get()
            if value and value.strip():
                return value.strip()

        # Try meta tags
        meta_title = self._extract_meta_title(response)
        if meta_title:
            cleaned = meta_title.replace('– We Work Remotely', '').replace('- We Work Remotely', '').strip()
            # Try to split company/title patterns and return the probable title
            _, probable_title = self._parse_company_and_title(cleaned)
            if probable_title:
                return probable_title

        # Last resort: document <title>
        doc_title = response.css('title::text').get()
        if doc_title:
            cleaned = doc_title.replace('– We Work Remotely', '').replace('- We Work Remotely', '').strip()
            _, probable_title = self._parse_company_and_title(cleaned)
            if probable_title:
                return probable_title

        return 'Unknown Title'
    
    def _extract_company(self, response):
        """Extract company name with JSON-LD, meta, and DOM fallbacks"""
        # Try JSON-LD first
        data = self._extract_from_json_ld(response)
        hiring_org = data.get('hiringOrganization')
        if isinstance(hiring_org, dict) and hiring_org.get('name'):
            return hiring_org['name'].strip()

        company_selectors = [
            '.company h2 a::text',
            '.company a::text',
            '.company::text',
            '.company-card h3::text',
            '.company-card .name::text',
            '.listing-header .company::text',
            '.listing-header .company a::text',
            '.listing-header-container .company::text',
            '.listing-header-container .company a::text',
            '.listing-company a::text',
            '.company-name::text',
        ]
        for sel in company_selectors:
            value = response.css(sel).get()
            if value and value.strip():
                return value.strip()

        # Parse from meta title if available (common pattern on WWR)
        meta_title = self._extract_meta_title(response)
        if meta_title:
            cleaned = meta_title.replace('– We Work Remotely', '').replace('- We Work Remotely', '').strip()
            company, _ = self._parse_company_and_title(cleaned)
            if company:
                return company

        # Fallback: parse from document title
        doc_title = response.css('title::text').get()
        if doc_title:
            cleaned = doc_title.replace('– We Work Remotely', '').replace('- We Work Remotely', '').strip()
            company, _ = self._parse_company_and_title(cleaned)
            if company:
                return company

        return 'Unknown Company'

    def _extract_meta_title(self, response):
        """Get a meaningful title from meta tags if present"""
        meta_candidates = [
            'meta[property="og:title"]::attr(content)',
            'meta[name="twitter:title"]::attr(content)',
        ]
        for sel in meta_candidates:
            value = response.css(sel).get()
            if value and value.strip():
                return value.strip()
        return ''

    def _parse_company_and_title(self, text):
        """Heuristically split company and title from combined text.
        Returns tuple (company, title). Either may be empty string if not inferred.
        Common WWR forms:
          - "Company – Job Title"
          - "Company is hiring a Job Title"
          - "Job Title at Company"
        """
        try:
            lowered = text.lower()
            # Pattern: Company is hiring a Job Title
            match = re.search(r'^(.*?)\s+is\s+hiring\s+(?:an?\s+)?(.+)$', text, re.IGNORECASE)
            if match:
                return match.group(1).strip(), match.group(2).strip()

            # Pattern: Job Title at Company
            match = re.search(r'^(.*?)\s+at\s+(.+)$', text, re.IGNORECASE)
            if match:
                return match.group(2).strip(), match.group(1).strip()

            # Pattern: Company – Job Title (en dash or hyphen)
            splitter = '–' if '–' in text else ('-' if '-' in text else None)
            if splitter:
                left, right = [part.strip() for part in text.split(splitter, 1)]
                # Heuristics: if right looks like a job title (contains common role terms), treat right as title
                role_terms = ['engineer', 'developer', 'designer', 'manager', 'devops', 'scientist', 'analyst', 'architect']
                if any(term in right.lower() for term in role_terms):
                    return left, right
                # Otherwise swap
                return right, left
        except Exception:
            pass
        return '', ''

    def _extract_from_json_ld(self, response):
        """Parse application/ld+json blocks for JobPosting data"""
        result = {}
        try:
            for script in response.css('script[type="application/ld+json"]::text').getall():
                script = script.strip()
                if not script:
                    continue
                data = json.loads(script)
                # Some pages wrap data in a list
                candidates = data if isinstance(data, list) else [data]
                for cand in candidates:
                    if isinstance(cand, dict) and cand.get('@type') in ('JobPosting', 'Posting'):
                        if 'title' in cand:
                            result['title'] = cand['title']
                        if 'hiringOrganization' in cand:
                            result['hiringOrganization'] = cand['hiringOrganization']
                        if 'datePosted' in cand:
                            result['datePosted'] = cand['datePosted']
                        return result
        except Exception:
            pass
        return result
    
    def _extract_job_id(self, url):
        """Extract job ID from URL"""
        # Extract ID from URL pattern like /remote-jobs/123456/job-title
        match = re.search(r'/remote-jobs/(\d+)/', url)
        return match.group(1) if match else url.split('/')[-1]
    
    def _extract_description(self, response):
        """Extract job description"""
        # Try multiple selectors for description
        description_selectors = [
            '.listing-container .listing-container-content',
            '.listing .listing-description',
            '#job-listing-show .listing-description',
        ]
        
        for selector in description_selectors:
            description = response.css(selector).get()
            if description:
                return description
        
        return ''
    
    def _extract_location(self, response):
        """Extract location information"""
        # WeWorkRemotely jobs are typically remote
        location_text = response.css('.listing-header .location::text').get()
        if location_text:
            return location_text.strip()
        
        # Default for WeWorkRemotely
        return 'Remote'
    
    def _extract_salary(self, response):
        """Extract salary information"""
        # Look for salary in various places
        salary_selectors = [
            '.listing-header .salary::text',
            '.compensation::text',
            '.listing-container:contains("salary") ::text',
        ]
        
        for selector in salary_selectors:
            salary = response.css(selector).get()
            if salary and any(char.isdigit() for char in salary):
                return salary.strip()
        
        return ''
    
    def _determine_job_type(self, response):
        """Determine job type from content"""
        content = response.text.lower()
        
        if any(term in content for term in ['contract', 'contractor', 'freelance']):
            return 'contract'
        elif any(term in content for term in ['part time', 'part-time', 'parttime']):
            return 'part_time'
        elif any(term in content for term in ['internship', 'intern']):
            return 'internship'
        else:
            return 'full_time'
    
    def _extract_tags(self, response):
        """Extract job tags/categories"""
        tags = []
        
        # Extract from breadcrumbs or category
        category_links = response.css('.breadcrumbs a::text').getall()
        for link in category_links:
            if link and 'remote' not in link.lower() and 'weworkremotely' not in link.lower():
                tags.append(link.strip().lower())
        
        # Extract from job title and description
        title_and_desc = f"{response.css('h1::text').get('')} {response.css('.listing-container::text').get('')}".lower()
        
        # Common tech keywords
        tech_keywords = [
            'python', 'javascript', 'react', 'node', 'django', 'flask',
            'aws', 'docker', 'kubernetes', 'sql', 'postgresql', 'mongodb',
            'frontend', 'backend', 'fullstack', 'devops', 'ml', 'ai'
        ]
        
        for keyword in tech_keywords:
            if keyword in title_and_desc:
                tags.append(keyword)
        
        return list(set(tags))  # Remove duplicates
    
    def _extract_skills(self, response):
        """Extract required skills"""
        skills = []
        content = response.css('.listing-container::text').getall()
        content_text = ' '.join(content).lower()
        
        # Common skill patterns
        skill_patterns = [
            r'(\w+)\s+years?\s+experience',
            r'experience\s+with\s+(\w+)',
            r'knowledge\s+of\s+(\w+)',
            r'proficient\s+in\s+(\w+)',
        ]
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, content_text)
            skills.extend(matches)
        
        # Filter and clean skills
        valid_skills = []
        for skill in skills:
            if len(skill) > 2 and skill.isalpha():
                valid_skills.append(skill.title())
        
        return list(set(valid_skills))[:10]  # Limit to 10 skills
    
    def _extract_posted_date(self, response):
        """Extract posting date; prefer JSON-LD, then page text; return timezone-aware datetime"""
        # JSON-LD datePosted if available
        data = self._extract_from_json_ld(response)
        iso_dt = data.get('datePosted')
        if iso_dt:
            try:
                # Try fromisoformat first
                return datetime.fromisoformat(iso_dt.replace('Z', '+00:00'))
            except Exception:
                pass

        date_text = response.css('.listing-date::text').get()
        if date_text:
            try:
                if 'ago' in date_text.lower():
                    return timezone.now()
                return datetime.strptime(date_text.strip(), '%Y-%m-%d')
            except ValueError:
                pass
        return timezone.now()