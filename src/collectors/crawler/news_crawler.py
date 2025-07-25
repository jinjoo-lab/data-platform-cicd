import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Any, Optional
from datetime import datetime


class ITWorldNewsCrawler:
    """ITWorld 웹사이트 전용 뉴스 크롤러"""
    
    def __init__(self, timeout: int = 15, max_retries: int = 3):
        """
        ITWorldNewsCrawler 초기화
        
        Args:
            timeout: HTTP 요청 타임아웃 (초)
            max_retries: 최대 재시도 횟수
        """
        self.base_url = "https://www.itworld.co.kr"
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'https://www.itworld.co.kr/'
        })
    
    def crawl_main_page_news(self, include_content: bool = False) -> Dict[str, Any]:
        """
        메인 페이지의 뉴스 목록을 크롤링합니다.
        
        Args:
            include_content: True이면 각 기사의 본문도 함께 수집
        
        Returns:
            뉴스 목록이 포함된 결과 딕셔너리
        """
        try:
            print("🔍 ITWorld 메인 페이지 뉴스 크롤링 시작...")
            if include_content:
                print("📖 각 기사의 세부 내용도 함께 수집합니다...")
            
            response = self._make_request(self.base_url)
            if not response:
                return self._create_error_result("메인 페이지에 접근할 수 없습니다.")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 전체 페이지에서 기사 링크들을 먼저 수집
            article_links = {}
            all_article_links = soup.find_all('a', href=lambda x: x and '/article/' in x)
            print(f"🔗 발견된 기사 링크: {len(all_article_links)}개")
            
            for link in all_article_links:
                title = link.get_text(strip=True)
                href = link.get('href')
                if title and len(title) > 10:  # 의미있는 제목만
                    # 제목을 정리해서 매칭 키로 사용
                    clean_title = self._clean_title_for_matching(title)
                    article_links[clean_title] = urljoin(self.base_url, href)
            
            print(f"📝 매칭용 제목-링크 매핑: {len(article_links)}개")
            
            # 뉴스 기사 수집
            news_list = []
            
            # 메인 뉴스 카드들 추출
            main_cards = soup.find_all('div', class_='card')
            print(f"📰 발견된 뉴스 카드: {len(main_cards)}개")
            
            for i, card in enumerate(main_cards):
                try:
                    news_item = self._extract_news_from_card(card, article_links)
                    if news_item:
                        news_list.append(news_item)
                        print(f"  ✅ 뉴스 {i+1}: {news_item.get('title', 'N/A')[:50]}...")
                except Exception as e:
                    print(f"  ❌ 카드 {i+1} 처리 중 오류: {str(e)}")
                    continue
            
            # 추가 뉴스 섹션들 확인
            content_rows = soup.find_all('div', class_='content-row-article')
            print(f"📑 추가 컨텐츠 행: {len(content_rows)}개")
            
            for row in content_rows:
                try:
                    # 메인 뉴스
                    main_article = row.find('div', class_='content-row-article__main')
                    if main_article:
                        main_card = main_article.find('div', class_='card')
                        if main_card:
                            news_item = self._extract_news_from_card(main_card, article_links)
                            if news_item and not any(n['title'] == news_item['title'] for n in news_list):
                                news_list.append(news_item)
                    
                    # 사이드 뉴스들
                    secondary_section = row.find('div', class_='content-row-article__secondary')
                    if secondary_section:
                        secondary_cards = secondary_section.find_all('div', class_='card')
                        for card in secondary_cards:
                            news_item = self._extract_news_from_card(card, article_links)
                            if news_item and not any(n['title'] == news_item['title'] for n in news_list):
                                news_list.append(news_item)
                                
                except Exception as e:
                    print(f"  ❌ 컨텐츠 행 처리 중 오류: {str(e)}")
                    continue
            
            # 중복 제거 (제목 기준)
            unique_news = []
            seen_titles = set()
            for news in news_list:
                if news['title'] not in seen_titles:
                    unique_news.append(news)
                    seen_titles.add(news['title'])
            
            # 세부 내용 수집 (옵션)
            if include_content:
                unique_news = self._collect_article_contents(unique_news)
            
            result = {
                'success': True,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'ITWorld 메인 페이지',
                'url': self.base_url,
                'total_news': len(unique_news),
                'news_list': unique_news,
                'categories': self._extract_categories(unique_news),
                'summary': self._generate_summary(unique_news),
                'content_included': include_content
            }
            
            print(f"✅ 크롤링 완료: {len(unique_news)}개의 고유 뉴스 수집")
            if include_content:
                content_count = len([n for n in unique_news if n.get('full_content')])
                print(f"📖 세부 내용 수집: {content_count}개 기사")
            
            return result
            
        except Exception as e:
            return self._create_error_result(f"크롤링 중 오류 발생: {str(e)}")
    
    def _clean_title_for_matching(self, title: str) -> str:
        """제목을 매칭을 위해 정리합니다."""
        import re
        # 불필요한 문자들 제거
        clean = re.sub(r'[^\w\s가-힣]', '', title.lower())
        # 연속된 공백을 하나로
        clean = re.sub(r'\s+', ' ', clean).strip()
        # 처음 50자만 사용 (매칭 정확도 향상)
        return clean[:50]
    
    def _extract_news_from_card(self, card, article_links: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """카드에서 뉴스 정보를 추출하고 링크를 매칭합니다."""
        try:
            news_item = {}
            
            # 제목 추출 (실제 구조에 맞게 수정)
            title_elem = card.find('h3', class_='card__title') or card.find('div', class_='card__title')
            if title_elem:
                news_item['title'] = title_elem.get_text(strip=True)
            
            # 제목이 없으면 다른 방법으로 찾기
            if not news_item.get('title'):
                # h2, h3 태그에서 제목 찾기
                for header_tag in ['h2', 'h3', 'h4']:
                    header = card.find(header_tag)
                    if header:
                        title_text = header.get_text(strip=True)
                        if len(title_text) > 10:  # 의미있는 제목만
                            news_item['title'] = title_text
                            break
            
            if not news_item.get('title'):
                return None
            
            # 제목을 이용해 링크 매칭
            clean_title = self._clean_title_for_matching(news_item['title'])
            
            # 정확히 매칭되는 링크 찾기
            matched_url = None
            for link_title, url in article_links.items():
                if clean_title == link_title:
                    matched_url = url
                    break
            
            # 정확한 매칭이 없으면 부분 매칭 시도
            if not matched_url:
                title_words = clean_title.split()
                if len(title_words) >= 3:  # 최소 3단어 이상일 때만
                    for link_title, url in article_links.items():
                        # 앞의 3단어가 모두 포함되어 있는지 확인
                        if all(word in link_title for word in title_words[:3]):
                            matched_url = url
                            break
            
            if matched_url:
                news_item['url'] = matched_url
                print(f"    🔗 링크 매칭 성공: {news_item['title'][:30]}...")
            else:
                print(f"    ⚠️  링크 매칭 실패: {news_item['title'][:30]}...")
            
            # 콘텐츠 타입 추출
            content_type_selectors = [
                'span.card__content-type',
                'div.card__content-type', 
                '.content-type',
                '.post-type'
            ]
            for selector in content_type_selectors:
                content_type = card.select_one(selector)
                if content_type:
                    news_item['content_type'] = content_type.get_text(strip=True)
                    break
            
            # 설명 추출
            description_selectors = [
                'p.card__description',
                'div.card__description',
                '.description',
                '.excerpt',
                'p'
            ]
            for selector in description_selectors:
                description = card.select_one(selector)
                if description:
                    desc_text = description.get_text(strip=True)
                    if len(desc_text) > 20:  # 의미있는 설명만
                        news_item['description'] = desc_text
                        break
            
            # 태그 추출
            tags = []
            tags_selectors = [
                'div.card__tags span.tag',
                '.tags .tag',
                '.category',
                '.topic'
            ]
            for selector in tags_selectors:
                tag_elements = card.select(selector)
                if tag_elements:
                    tags = [tag.get_text(strip=True) for tag in tag_elements if tag.get_text(strip=True)]
                    break
            news_item['tags'] = tags
            
            # 추가 정보 추출
            info_elements = card.find_all(['div', 'span'], class_=lambda x: x and 'info' in x)
            for info in info_elements:
                info_text = info.get_text(strip=True)
                # 날짜 패턴 찾기
                date_match = re.search(r'(\d{4})\.(\d{1,2})\.(\d{1,2})', info_text)
                if date_match:
                    news_item['publish_date'] = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"
                
                # 시간 패턴 찾기
                time_match = re.search(r'(\d{1,2}분)', info_text)
                if time_match:
                    news_item['read_time'] = time_match.group(1)
                
                # 작성자 정보
                if 'By' in info_text:
                    author_match = re.search(r'By\s+(.+?)(?:\s|$)', info_text)
                    if author_match:
                        news_item['author'] = author_match.group(1).strip()
            
            # 전체 카드 텍스트에서 날짜와 작성자 찾기
            if not news_item.get('publish_date') or not news_item.get('author'):
                card_text = card.get_text()
                
                # 날짜 찾기
                if not news_item.get('publish_date'):
                    date_match = re.search(r'(\d{4})\.(\d{1,2})\.(\d{1,2})', card_text)
                    if date_match:
                        news_item['publish_date'] = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"
                
                # 작성자 찾기
                if not news_item.get('author'):
                    author_match = re.search(r'By\s+(.+?)(?:\s|$)', card_text)
                    if author_match:
                        news_item['author'] = author_match.group(1).strip()
            
            # 이미지 추출
            image_elem = card.find('img')
            if image_elem:
                image_src = image_elem.get('src') or image_elem.get('data-src')
                if image_src:
                    news_item['image_url'] = urljoin(self.base_url, image_src)
                    news_item['image_alt'] = image_elem.get('alt', '')
            
            # 메타데이터
            news_item['crawled_at'] = datetime.now().isoformat()
            news_item['source'] = 'ITWorld'
            
            print(f"    ✅ 추출 성공: {news_item.get('title', 'No title')[:50]}...")
            return news_item
            
        except Exception as e:
            print(f"    ❌ 카드에서 뉴스 추출 중 오류: {str(e)}")
            return None
    
    def _collect_article_contents(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        뉴스 목록의 각 기사에 대해 세부 내용을 수집합니다.
        
        Args:
            news_list: 뉴스 목록
            
        Returns:
            세부 내용이 추가된 뉴스 목록
        """
        print(f"\n📖 {len(news_list)}개 기사의 세부 내용 수집 중...")
        
        for i, news in enumerate(news_list):
            if not news.get('url'):
                print(f"  ⚠️  기사 {i+1}: URL이 없어 본문을 가져올 수 없습니다.")
                continue
            
            try:
                print(f"  📄 기사 {i+1}/{len(news_list)}: {news.get('title', 'N/A')[:40]}...")
                
                # 기사 본문 가져오기
                article_content = self.get_article_content(news['url'])
                
                if article_content.get('success'):
                    # 본문 내용 추가
                    news['full_content'] = article_content.get('content', '')
                    news['content_length'] = len(news['full_content'])
                    
                    # 추가로 얻은 정보가 있으면 업데이트
                    if article_content.get('author') and not news.get('author'):
                        news['author'] = article_content.get('author')
                    
                    if article_content.get('publish_date') and not news.get('publish_date'):
                        news['publish_date'] = article_content.get('publish_date')
                    
                    print(f"    ✅ 성공 ({len(news['full_content'])}자)")
                else:
                    print(f"    ❌ 실패: {article_content.get('error', 'Unknown error')}")
                    news['full_content'] = ''
                    news['content_length'] = 0
                
                # 요청 간 딜레이 (서버 부하 방지)
                time.sleep(1)
                
            except Exception as e:
                print(f"    ❌ 기사 {i+1} 내용 수집 중 오류: {str(e)}")
                news['full_content'] = ''
                news['content_length'] = 0
                continue
        
        return news_list

    def crawl_category_news(self, category_url: str, max_pages: int = 3, include_content: bool = False) -> Dict[str, Any]:
        """
        특정 카테고리의 뉴스를 크롤링합니다.
        
        Args:
            category_url: 카테고리 페이지 URL
            max_pages: 최대 크롤링할 페이지 수
            include_content: True이면 각 기사의 본문도 함께 수집
            
        Returns:
            카테고리 뉴스 목록
        """
        try:
            print(f"🔍 카테고리 뉴스 크롤링 시작: {category_url}")
            if include_content:
                print("📖 각 기사의 세부 내용도 함께 수집합니다...")
            
            all_news = []
            
            for page in range(1, max_pages + 1):
                page_url = f"{category_url}?page={page}" if page > 1 else category_url
                
                response = self._make_request(page_url)
                if not response:
                    print(f"  ❌ 페이지 {page} 접근 실패")
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 페이지에서 기사 링크들 수집
                article_links = {}
                page_article_links = soup.find_all('a', href=lambda x: x and '/article/' in x)
                
                for link in page_article_links:
                    title = link.get_text(strip=True)
                    href = link.get('href')
                    if title and len(title) > 10:  # 의미있는 제목만
                        clean_title = self._clean_title_for_matching(title)
                        article_links[clean_title] = urljoin(self.base_url, href)
                
                cards = soup.find_all('div', class_='card')
                
                if not cards:
                    print(f"  ⚠️ 페이지 {page}에서 뉴스를 찾을 수 없습니다.")
                    break
                
                print(f"  📄 페이지 {page}: {len(cards)}개 뉴스 발견, {len(article_links)}개 링크 매핑")
                
                for card in cards:
                    news_item = self._extract_news_from_card(card, article_links)
                    if news_item:
                        all_news.append(news_item)
                
                # 페이지 간 요청 간격
                time.sleep(1)
            
            # 중복 제거
            unique_news = []
            seen_titles = set()
            for news in all_news:
                if news['title'] not in seen_titles:
                    unique_news.append(news)
                    seen_titles.add(news['title'])
            
            # 세부 내용 수집 (옵션)
            if include_content:
                unique_news = self._collect_article_contents(unique_news)
            
            result = {
                'success': True,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': f'ITWorld 카테고리',
                'url': category_url,
                'pages_crawled': page,
                'total_news': len(unique_news),
                'news_list': unique_news,
                'categories': self._extract_categories(unique_news),
                'summary': self._generate_summary(unique_news),
                'content_included': include_content
            }
            
            print(f"✅ 카테고리 크롤링 완료: {len(unique_news)}개의 고유 뉴스 수집")
            if include_content:
                content_count = len([n for n in unique_news if n.get('full_content')])
                print(f"📖 세부 내용 수집: {content_count}개 기사")
            
            return result
            
        except Exception as e:
            return self._create_error_result(f"카테고리 크롤링 중 오류: {str(e)}")
    
    def get_article_content(self, article_url: str) -> Dict[str, Any]:
        """
        개별 기사의 전체 내용을 가져옵니다.
        
        Args:
            article_url: 기사 URL
            
        Returns:
            기사 전체 내용
        """
        try:
            response = self._make_request(article_url)
            if not response:
                return self._create_error_result("기사에 접근할 수 없습니다.")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 기사 내용 추출 (ITWorld 특화)
            article_content = {
                'url': article_url,
                'title': '',
                'content': '',
                'publish_date': '',
                'author': '',
                'tags': [],
                'category': ''
            }
            
            # 제목 추출
            title_selectors = [
                'h1.article-title',
                'h1.post-title', 
                '.article-header h1',
                '.content-header h1',
                'h1',
                '.page-title h1'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    article_content['title'] = title_elem.get_text(strip=True)
                    break
            
            # 기사 본문 추출 (ITWorld 특화 선택자들)
            content_selectors = [
                '.article-content',
                '.post-content', 
                '.content-body',
                '.article-body',
                '.story-body',
                '[data-module="ArticleBody"]',
                '.entry-content',
                'article .content',
                '.main-content'
            ]
            
            content_found = False
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 불필요한 요소 제거
                    for unwanted in content_elem.find_all([
                        'script', 'style', 'aside', 'nav', 'footer', 
                        '.advertisement', '.ad', '.social-share',
                        '.related-articles', '.comments'
                    ]):
                        unwanted.decompose()
                    
                    # 텍스트 추출
                    paragraphs = content_elem.find_all(['p', 'div'], recursive=True)
                    content_parts = []
                    
                    for p in paragraphs:
                        text = p.get_text(separator=' ', strip=True)
                        # 의미있는 문단만 (길이가 20자 이상이고 광고성 텍스트가 아닌)
                        if (len(text) > 20 and 
                            not any(ad_word in text.lower() for ad_word in 
                                   ['advertisement', '광고', 'sponsored', '후원'])):
                            content_parts.append(text)
                    
                    if content_parts:
                        article_content['content'] = '\n\n'.join(content_parts)
                        content_found = True
                        break
            
            # 기본 문단 추출 (위 방법이 실패한 경우)
            if not content_found:
                main_content = soup.find('main') or soup.find('article') or soup
                paragraphs = main_content.find_all('p')
                content_parts = []
                
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if len(text) > 50:  # 더 긴 문단만
                        content_parts.append(text)
                
                if content_parts:
                    article_content['content'] = '\n\n'.join(content_parts[:10])  # 최대 10개 문단
            
            # 작성자 추출
            author_selectors = [
                '.article-author',
                '.author-name',
                '.byline .author',
                '.post-author',
                '[rel="author"]'
            ]
            
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    article_content['author'] = author_elem.get_text(strip=True)
                    break
            
            # 날짜 추출
            date_selectors = [
                '.article-date',
                '.publish-date', 
                '.post-date',
                'time[datetime]',
                '.date-published'
            ]
            
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    # 날짜 패턴 찾기
                    date_match = re.search(r'(\d{4})[-./](\d{1,2})[-./](\d{1,2})', date_text)
                    if date_match:
                        article_content['publish_date'] = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"
                        break
            
            # 카테고리/태그 추출
            tag_selectors = [
                '.article-tags a',
                '.post-categories a',
                '.tags a',
                '.category a'
            ]
            
            for selector in tag_selectors:
                tag_elements = soup.select(selector)
                if tag_elements:
                    article_content['tags'] = [tag.get_text(strip=True) for tag in tag_elements]
                    break
            
            article_content['crawled_at'] = datetime.now().isoformat()
            article_content['success'] = True
            
            return article_content
            
        except Exception as e:
            return self._create_error_result(f"기사 내용 수집 중 오류: {str(e)}")
    
    def _extract_categories(self, news_list: List[Dict]) -> Dict[str, int]:
        """뉴스 목록에서 카테고리 통계를 추출합니다."""
        categories = {}
        for news in news_list:
            for tag in news.get('tags', []):
                categories[tag] = categories.get(tag, 0) + 1
        return dict(sorted(categories.items(), key=lambda x: x[1], reverse=True))
    
    def _generate_summary(self, news_list: List[Dict]) -> Dict[str, Any]:
        """뉴스 목록의 요약 정보를 생성합니다."""
        if not news_list:
            return {}
        
        # 날짜별 분포
        dates = {}
        for news in news_list:
            date = news.get('publish_date', 'Unknown')
            dates[date] = dates.get(date, 0) + 1
        
        # 컨텐츠 타입별 분포
        content_types = {}
        for news in news_list:
            content_type = news.get('content_type', 'Unknown')
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        return {
            'total_articles': len(news_list),
            'date_distribution': dates,
            'content_type_distribution': content_types,
            'latest_date': max([n.get('publish_date', '') for n in news_list if n.get('publish_date')], default=''),
            'has_images': len([n for n in news_list if n.get('image_url')])
        }
    
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """HTTP 요청을 수행합니다."""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                print(f"  ⚠️ 요청 실패 (시도 {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
        return None
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """오류 결과를 생성합니다."""
        return {
            'success': False,
            'error': error_message,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'news_list': []
        } 