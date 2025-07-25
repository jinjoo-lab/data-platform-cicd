import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse
import re
from typing import Dict, List, Any, Optional
import time


class WebAnalyzer:
    """웹사이트를 크롤링하고 분석하는 클래스"""
    
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        """
        WebAnalyzer 초기화
        
        Args:
            timeout: HTTP 요청 타임아웃 (초)
            max_retries: 최대 재시도 횟수
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def crawl_website(self, url: str) -> Dict[str, Any]:
        """
        웹사이트를 크롤링하고 기본 정보를 수집합니다.
        
        Args:
            url: 크롤링할 웹사이트 URL
            
        Returns:
            크롤링 결과를 담은 딕셔너리
        """
        try:
            # URL 정규화
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            print(f"크롤링 시작: {url}")
            
            # HTTP 요청
            response = self._make_request(url)
            if not response:
                return self._create_error_result(url, "웹사이트에 접근할 수 없습니다.")
            
            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 웹사이트 분석
            analysis_result = {
                'url': url,
                'status_code': response.status_code,
                'success': True,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'basic_info': self._extract_basic_info(soup),
                'content_analysis': self._analyze_content(soup),
                'structure_analysis': self._analyze_structure(soup),
                'data_opportunities': self._identify_data_opportunities(soup)
            }
            
            return analysis_result
            
        except Exception as e:
            return self._create_error_result(url, f"크롤링 중 오류 발생: {str(e)}")
    
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """HTTP 요청을 수행합니다."""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                print(f"요청 실패 (시도 {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 지수 백오프
        return None
    
    def _extract_basic_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """웹사이트의 기본 정보를 추출합니다."""
        title = soup.find('title')
        description = soup.find('meta', attrs={'name': 'description'})
        keywords = soup.find('meta', attrs={'name': 'keywords'})
        
        return {
            'title': title.text.strip() if title else 'No title found',
            'description': description.get('content', 'No description found') if description else 'No description found',
            'keywords': keywords.get('content', 'No keywords found') if keywords else 'No keywords found'
        }
    
    def _analyze_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """웹사이트의 콘텐츠를 분석합니다."""
        # 텍스트 콘텐츠 분석
        text_content = soup.get_text()
        words = re.findall(r'\w+', text_content.lower())
        
        # 이미지 분석
        images = soup.find_all('img')
        
        # 링크 분석
        links = soup.find_all('a', href=True)
        
        return {
            'text_stats': {
                'total_words': len(words),
                'unique_words': len(set(words)),
                'most_common_words': self._get_most_common_words(words, 10)
            },
            'media_stats': {
                'total_images': len(images),
                'images_with_alt': len([img for img in images if img.get('alt')])
            },
            'link_stats': {
                'total_links': len(links),
                'internal_links': len([link for link in links if self._is_internal_link(link.get('href'))]),
                'external_links': len([link for link in links if not self._is_internal_link(link.get('href'))])
            }
        }
    
    def _analyze_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """웹사이트의 HTML 구조를 분석합니다."""
        # HTML 태그 분석
        all_tags = soup.find_all()
        tag_counts = {}
        for tag in all_tags:
            tag_name = tag.name
            tag_counts[tag_name] = tag_counts.get(tag_name, 0) + 1
        
        # 테이블 분석
        tables = soup.find_all('table')
        
        # 폼 분석
        forms = soup.find_all('form')
        
        # 리스트 분석
        lists = soup.find_all(['ul', 'ol'])
        
        return {
            'tag_distribution': dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:15]),
            'structural_elements': {
                'tables': len(tables),
                'forms': len(forms),
                'lists': len(lists),
                'headings': len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])),
                'paragraphs': len(soup.find_all('p'))
            }
        }
    
    def _identify_data_opportunities(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """크롤링 가능한 데이터 기회를 식별합니다."""
        opportunities = []
        
        # 테이블 데이터
        tables = soup.find_all('table')
        for i, table in enumerate(tables):
            rows = table.find_all('tr')
            cols = len(table.find_all('th')) or len(table.find_all('td'))
            if rows and cols:
                opportunities.append({
                    'type': 'table',
                    'description': f'테이블 #{i+1} ({len(rows)}행 x {cols}열)',
                    'potential_data': '구조화된 표 데이터'
                })
        
        # 리스트 데이터
        lists = soup.find_all(['ul', 'ol'])
        for i, list_elem in enumerate(lists):
            items = list_elem.find_all('li')
            if len(items) > 3:  # 의미있는 리스트만
                opportunities.append({
                    'type': 'list',
                    'description': f'리스트 #{i+1} ({len(items)}개 항목)',
                    'potential_data': '목록 형태의 데이터'
                })
        
        # 반복되는 패턴 (예: 제품, 기사 등)
        common_classes = self._find_repeated_patterns(soup)
        for class_name, count in common_classes.items():
            if count > 3:  # 3개 이상 반복되는 패턴
                opportunities.append({
                    'type': 'repeated_pattern',
                    'description': f'반복 패턴: .{class_name} ({count}개)',
                    'potential_data': '반복되는 구조화된 콘텐츠'
                })
        
        # 폼 데이터
        forms = soup.find_all('form')
        for i, form in enumerate(forms):
            inputs = form.find_all(['input', 'select', 'textarea'])
            if inputs:
                opportunities.append({
                    'type': 'form',
                    'description': f'폼 #{i+1} ({len(inputs)}개 입력 필드)',
                    'potential_data': '사용자 입력 데이터 구조'
                })
        
        return {
            'total_opportunities': len(opportunities),
            'opportunities': opportunities,
            'recommendations': self._generate_recommendations(opportunities)
        }
    
    def _get_most_common_words(self, words: List[str], limit: int) -> List[tuple]:
        """가장 자주 사용되는 단어들을 반환합니다."""
        word_counts = {}
        for word in words:
            if len(word) > 2:  # 2글자 이상만
                word_counts[word] = word_counts.get(word, 0) + 1
        
        return sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def _is_internal_link(self, href: str) -> bool:
        """내부 링크인지 판단합니다."""
        if not href:
            return False
        return href.startswith('/') or href.startswith('#') or not href.startswith('http')
    
    def _find_repeated_patterns(self, soup: BeautifulSoup) -> Dict[str, int]:
        """반복되는 CSS 클래스 패턴을 찾습니다."""
        class_counts = {}
        for elem in soup.find_all(class_=True):
            for class_name in elem.get('class', []):
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        return {k: v for k, v in class_counts.items() if v > 1}
    
    def _generate_recommendations(self, opportunities: List[Dict]) -> List[str]:
        """크롤링 추천사항을 생성합니다."""
        recommendations = []
        
        table_count = len([o for o in opportunities if o['type'] == 'table'])
        list_count = len([o for o in opportunities if o['type'] == 'list'])
        pattern_count = len([o for o in opportunities if o['type'] == 'repeated_pattern'])
        
        if table_count > 0:
            recommendations.append(f"📊 {table_count}개의 테이블이 발견되었습니다. 구조화된 데이터 추출에 적합합니다.")
        
        if list_count > 0:
            recommendations.append(f"📝 {list_count}개의 리스트가 발견되었습니다. 목록 데이터 수집이 가능합니다.")
        
        if pattern_count > 0:
            recommendations.append(f"🔄 {pattern_count}개의 반복 패턴이 발견되었습니다. 대량 데이터 수집에 유리합니다.")
        
        if not opportunities:
            recommendations.append("⚠️ 특별한 데이터 패턴이 발견되지 않았습니다. 텍스트 콘텐츠 추출을 고려해보세요.")
        
        return recommendations
    
    def _create_error_result(self, url: str, error_message: str) -> Dict[str, Any]:
        """오류 결과를 생성합니다."""
        return {
            'url': url,
            'success': False,
            'error': error_message,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        } 