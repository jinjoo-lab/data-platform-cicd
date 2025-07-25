#!/usr/bin/env python3
"""
ITWorld 뉴스 크롤러 메인 인터페이스
ITWorld 웹사이트에서 뉴스 데이터를 수집하고 다양한 형태로 저장하는 기능을 제공합니다.
"""

import argparse
import sys
import os
from typing import Dict, Any

# 상위 디렉터리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news_crawler import ITWorldNewsCrawler
from news_formatter import NewsFormatter


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="ITWorld 웹사이트에서 뉴스를 크롤링합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python news_main.py --main-page                    # 메인 페이지 뉴스 수집
  python news_main.py --main-page --save-json        # JSON으로 저장
  python news_main.py --main-page --save-csv         # CSV로 저장  
  python news_main.py --main-page --save-html        # HTML 보고서 생성
  python news_main.py --main-page --include-content  # 본문 내용도 함께 수집
  python news_main.py --category "https://www.itworld.co.kr/news/ai" --pages 2  # 카테고리별 수집
  python news_main.py --category "https://www.itworld.co.kr/news/ai" --include-content  # 카테고리 + 본문
  python news_main.py --interactive                  # 대화형 모드
        """
    )
    
    # 크롤링 모드
    parser.add_argument(
        '--main-page', '-m',
        action='store_true',
        help='메인 페이지 뉴스 크롤링'
    )
    
    parser.add_argument(
        '--category', '-c',
        help='특정 카테고리 URL 크롤링'
    )
    
    parser.add_argument(
        '--pages', '-p',
        type=int,
        default=3,
        help='카테고리 크롤링 시 최대 페이지 수 (기본값: 3)'
    )
    
    parser.add_argument(
        '--include-content', '-f',
        action='store_true',
        help='각 기사의 세부 내용(본문)도 함께 수집'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='대화형 모드로 실행'
    )
    
    # 출력 옵션
    parser.add_argument(
        '--save-json', '-j',
        action='store_true',
        help='결과를 JSON 파일로 저장'
    )
    
    parser.add_argument(
        '--save-csv', '-v',
        action='store_true',
        help='결과를 CSV 파일로 저장'
    )
    
    parser.add_argument(
        '--save-html', '-w',
        action='store_true',
        help='HTML 보고서 생성'
    )
    
    parser.add_argument(
        '--detailed', '-d',
        action='store_true',
        help='상세한 뉴스 목록 출력'
    )
    
    parser.add_argument(
        '--max-display', '-n',
        type=int,
        default=10,
        help='화면에 표시할 최대 기사 수 (기본값: 10)'
    )
    
    # 설정 옵션
    parser.add_argument(
        '--timeout', '-t',
        type=int,
        default=15,
        help='HTTP 요청 타임아웃 (기본값: 15초)'
    )
    
    args = parser.parse_args()
    
    # 크롤러와 포매터 초기화
    crawler = ITWorldNewsCrawler(timeout=args.timeout)
    formatter = NewsFormatter()
    
    if args.interactive or (not args.main_page and not args.category):
        run_interactive_mode(crawler, formatter, args)
    else:
        run_crawling_mode(crawler, formatter, args)


def run_interactive_mode(crawler: ITWorldNewsCrawler, formatter: NewsFormatter, args):
    """대화형 모드 실행"""
    print("🌐 ITWorld 뉴스 크롤러 대화형 모드")
    print("=" * 60)
    print("ITWorld 웹사이트에서 뉴스를 수집하고 분석합니다.")
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.")
    print()
    
    while True:
        try:
            print("\n📋 크롤링 옵션:")
            print("  1. 메인 페이지 뉴스 수집")
            print("  2. 카테고리별 뉴스 수집")
            print("  3. 개별 기사 내용 수집")
            print("  4. 종료")
            
            choice = input("\n선택하세요 (1-4): ").strip()
            
            if choice in ['4', 'quit', 'exit', 'q']:
                print("프로그램을 종료합니다.")
                break
            
            elif choice == '1':
                include_content = input("기사 본문도 함께 수집하시겠습니까? (y/n, 기본값: n): ").strip().lower()
                include_content = include_content in ['y', 'yes']
                
                print("\n🔍 메인 페이지 뉴스 수집 중...")
                if include_content:
                    print("📖 각 기사의 세부 내용도 함께 수집합니다...")
                result = crawler.crawl_main_page_news(include_content=include_content)
                display_and_save_results(result, formatter, args)
            
            elif choice == '2':
                category_url = input("카테고리 URL을 입력하세요: ").strip()
                if not category_url:
                    print("❌ URL을 입력해주세요.")
                    continue
                
                pages = input(f"크롤링할 페이지 수 (기본값: {args.pages}): ").strip()
                max_pages = int(pages) if pages.isdigit() else args.pages
                
                include_content = input("기사 본문도 함께 수집하시겠습니까? (y/n, 기본값: n): ").strip().lower()
                include_content = include_content in ['y', 'yes']
                
                print(f"\n🔍 카테고리 뉴스 수집 중... (최대 {max_pages}페이지)")
                if include_content:
                    print("📖 각 기사의 세부 내용도 함께 수집합니다...")
                result = crawler.crawl_category_news(category_url, max_pages, include_content=include_content)
                display_and_save_results(result, formatter, args)
            
            elif choice == '3':
                article_url = input("기사 URL을 입력하세요: ").strip()
                if not article_url:
                    print("❌ URL을 입력해주세요.")
                    continue
                
                print("\n📖 기사 내용 수집 중...")
                article_result = crawler.get_article_content(article_url)
                if article_result.get('success'):
                    print(f"\n제목: {article_result.get('title', 'N/A')}")
                    print(f"URL: {article_result.get('url', 'N/A')}")
                    content = article_result.get('content', '')
                    if content:
                        print(f"내용 (처음 500자):\n{content[:500]}...")
                        if len(content) > 500:
                            print(f"\n... (총 {len(content)}자)")
                    else:
                        print("내용을 가져올 수 없습니다.")
                else:
                    print(f"❌ 오류: {article_result.get('error', 'Unknown error')}")
            
            else:
                print("❌ 올바른 선택지를 입력해주세요.")
                
        except KeyboardInterrupt:
            print("\n\n프로그램을 종료합니다.")
            break
        except EOFError:
            print("\n프로그램을 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 오류가 발생했습니다: {str(e)}")


def run_crawling_mode(crawler: ITWorldNewsCrawler, formatter: NewsFormatter, args):
    """명령행 크롤링 모드 실행"""
    if args.main_page:
        print("🔍 ITWorld 메인 페이지 뉴스 수집 중...")
        if args.include_content:
            print("📖 각 기사의 세부 내용도 함께 수집합니다...")
        result = crawler.crawl_main_page_news(include_content=args.include_content)
        display_and_save_results(result, formatter, args)
    
    elif args.category:
        print(f"🔍 카테고리 뉴스 수집 중: {args.category}")
        print(f"최대 {args.pages}페이지까지 수집합니다...")
        if args.include_content:
            print("📖 각 기사의 세부 내용도 함께 수집합니다...")
        result = crawler.crawl_category_news(args.category, args.pages, include_content=args.include_content)
        display_and_save_results(result, formatter, args)


def display_and_save_results(result: Dict[str, Any], formatter: NewsFormatter, args):
    """결과를 화면에 표시하고 파일로 저장합니다."""
    if not result.get('success', False):
        print(formatter._format_error_result(result))
        return
    
    # 화면 출력
    if args.detailed:
        print(formatter.format_detailed_news(result, args.max_display))
    else:
        print(formatter.format_news_summary(result))
    
    # 파일 저장
    saved_files = []
    data_dir = formatter._get_today_data_dir()
    
    if args.save_json or args.save_csv or args.save_html:
        print(f"\n💾 데이터 저장 위치: {data_dir}")
    
    if args.save_json:
        json_file = formatter.save_to_json(result)
        saved_files.append(f"📁 JSON: {os.path.basename(json_file)}")
    
    if args.save_csv:
        csv_file = formatter.save_to_csv(result)
        if csv_file:
            saved_files.append(f"📊 CSV: {os.path.basename(csv_file)}")
    
    if args.save_html:
        html_file = formatter.create_html_report(result)
        saved_files.append(f"🌐 HTML: {os.path.basename(html_file)}")
    
    if saved_files:
        print("📋 저장된 파일:")
        for file_info in saved_files:
            print(f"  {file_info}")
        
        # 디렉터리 구조 안내
        print(f"\n📂 전체 경로: {data_dir}")
        print("💡 동일한 날짜의 기존 파일들은 자동으로 삭제되고 새로 저장됩니다.")


def show_categories():
    """주요 ITWorld 카테고리 URL들을 보여줍니다."""
    categories = {
        "인공지능": "https://www.itworld.co.kr/news/ai",
        "클라우드": "https://www.itworld.co.kr/news/cloud",
        "보안": "https://www.itworld.co.kr/news/security",
        "소프트웨어 개발": "https://www.itworld.co.kr/news/development",
        "모바일": "https://www.itworld.co.kr/news/mobile",
        "네트워크": "https://www.itworld.co.kr/news/network",
        "데이터센터": "https://www.itworld.co.kr/news/datacenter"
    }
    
    print("\n📂 주요 ITWorld 카테고리:")
    for name, url in categories.items():
        print(f"  • {name}: {url}")


if __name__ == "__main__":
    main() 