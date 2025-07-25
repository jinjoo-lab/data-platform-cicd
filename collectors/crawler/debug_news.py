#!/usr/bin/env python3
"""
ITWorld 사이트 구조 디버깅 스크립트
"""

import requests
from bs4 import BeautifulSoup

def debug_itworld_structure():
    """ITWorld 사이트의 HTML 구조를 디버깅합니다."""
    url = "https://www.itworld.co.kr"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("🔍 ITWorld 사이트 구조 분석")
        print("=" * 50)
        
        # 카드 요소들 찾기
        cards = soup.find_all('div', class_='card')
        print(f"📰 발견된 카드 수: {len(cards)}")
        
        # 첫 번째 카드 구조 분석
        if cards:
            print("\n📑 첫 번째 카드 구조:")
            first_card = cards[0]
            print(f"카드 HTML:\n{first_card.prettify()[:1500]}...")
            
            # 제목 요소 찾기
            title_elem = first_card.find('h3', class_='card__title') or first_card.find('div', class_='card__title')
            print(f"\n제목 요소: {title_elem}")
            
            if title_elem:
                title_link = title_elem.find('a')
                print(f"제목 링크: {title_link}")
                if title_link:
                    print(f"제목 텍스트: {title_link.get_text(strip=True)}")
                    print(f"링크 URL: {title_link.get('href')}")
            
            # 카드 내부의 모든 링크 찾기
            print(f"\n🔗 카드 내부의 모든 링크:")
            all_links = first_card.find_all('a', href=True)
            for i, link in enumerate(all_links):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                print(f"  링크 {i+1}: {href} | 텍스트: {text[:50]}...")
            
            # 다른 요소들 확인
            content_type = first_card.find('span', class_='card__content-type')
            print(f"\n콘텐츠 타입: {content_type}")
            
            description = first_card.find('p', class_='card__description')
            print(f"설명: {description}")
            
            tags_container = first_card.find('div', class_='card__tags')
            print(f"태그 컨테이너: {tags_container}")
            
            if tags_container:
                tags = tags_container.find_all('span', class_='tag')
                print(f"태그들: {[tag.get_text(strip=True) for tag in tags]}")
        
        # 두 번째, 세 번째 카드도 확인
        for card_idx in [1, 2]:
            if len(cards) > card_idx:
                print(f"\n📑 카드 #{card_idx + 1} 링크 분석:")
                card = cards[card_idx]
                links = card.find_all('a', href=True)
                for i, link in enumerate(links):
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    print(f"  링크 {i+1}: {href} | 텍스트: {text[:30]}...")
        
        # 다른 뉴스 구조 찾기
        print("\n🔍 다른 뉴스 구조 찾기:")
        
        # 기사 제목들 찾기 (다양한 선택자 시도)
        selectors = [
            'h1', 'h2', 'h3',
            '.card__title a',
            '.article-title',
            '.post-title',
            'a[href*="/article/"]',
            'a[href*="/news/"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                print(f"선택자 '{selector}': {len(elements)}개 발견")
                for i, elem in enumerate(elements[:3]):  # 처음 3개만 표시
                    text = elem.get_text(strip=True)
                    if len(text) > 10:  # 의미있는 텍스트만
                        href = elem.get('href', '') if elem.name == 'a' else 'N/A'
                        print(f"  {i+1}. {text[:80]}... | href: {href}")
        
    except Exception as e:
        print(f"❌ 오류: {str(e)}")

if __name__ == "__main__":
    debug_itworld_structure() 