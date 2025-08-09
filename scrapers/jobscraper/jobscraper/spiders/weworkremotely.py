# scrapers/jobscraper/spiders/weworkremotely.py
import scrapy
import re
from urllib.parse import urljoin
from datetime import datetime
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
        """Extract job title"""
        title = response.css('h1.page-title::text').get()
        if not title:
            title = response.css('.listing-header h2::text').get()
        return title.strip() if title else 'Unknown Title'
    
    def _extract_company(self, response):
        """Extract company name"""
        company = response.css('.company h2 a::text').get()
        if not company:
            company = response.css('.listing-header .company::text').get()
        return company.strip() if company else 'Unknown Company'
    
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
        """Extract posting date"""
        date_text = response.css('.listing-date::text').get()
        
        if date_text:
            # Try to parse common date formats
            try:
                # Handle formats like "2 days ago", "1 week ago", etc.
                if 'ago' in date_text:
                    return datetime.now()  # For now, just use current time
                else:
                    # Try to parse actual dates
                    return datetime.strptime(date_text.strip(), '%Y-%m-%d')
            except ValueError:
                pass
        
        return datetime.now()  # Default to now