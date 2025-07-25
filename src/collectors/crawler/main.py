#!/usr/bin/env python3
"""
웹 크롤러 메인 인터페이스
사용자가 웹사이트 URL을 입력하면 크롤링하고 분석 결과를 보여줍니다.
"""

import argparse
import sys
import os

# 상위 디렉터리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.web_analyzer import WebAnalyzer
from crawler.data_formatter import DataFormatter


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="웹사이트를 크롤링하고 분석합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python main.py --url https://example.com
  python main.py --url example.com --save-json
  python main.py --interactive
        """
    )
    
    parser.add_argument(
        '--url', '-u',
        help='분석할 웹사이트 URL'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='대화형 모드로 실행'
    )
    
    parser.add_argument(
        '--save-json', '-s',
        action='store_true',
        help='결과를 JSON 파일로 저장'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='JSON 출력 파일명'
    )
    
    parser.add_argument(
        '--timeout', '-t',
        type=int,
        default=10,
        help='HTTP 요청 타임아웃 (기본값: 10초)'
    )
    
    args = parser.parse_args()
    
    # WebAnalyzer와 DataFormatter 초기화
    analyzer = WebAnalyzer(timeout=args.timeout)
    formatter = DataFormatter()
    
    if args.interactive or not args.url:
        run_interactive_mode(analyzer, formatter, args)
    else:
        analyze_single_url(args.url, analyzer, formatter, args)


def run_interactive_mode(analyzer: WebAnalyzer, formatter: DataFormatter, args):
    """대화형 모드 실행"""
    print("🌐 웹 크롤러 대화형 모드")
    print("=" * 50)
    print("웹사이트 URL을 입력하면 크롤링하고 분석합니다.")
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.")
    print()
    
    while True:
        try:
            url = input("분석할 웹사이트 URL을 입력하세요: ").strip()
            
            if url.lower() in ['quit', 'exit', 'q']:
                print("프로그램을 종료합니다.")
                break
            
            if not url:
                print("❌ URL을 입력해주세요.")
                continue
            
            print()
            analyze_single_url(url, analyzer, formatter, args)
            print()
            
            # 계속할지 물어보기
            continue_choice = input("다른 웹사이트를 분석하시겠습니까? (y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes', '']:
                print("프로그램을 종료합니다.")
                break
            print()
            
        except KeyboardInterrupt:
            print("\n\n프로그램을 종료합니다.")
            break
        except EOFError:
            print("\n프로그램을 종료합니다.")
            break


def analyze_single_url(url: str, analyzer: WebAnalyzer, formatter: DataFormatter, args):
    """단일 URL 분석"""
    print(f"🔍 웹사이트 분석 중: {url}")
    print("잠시만 기다려주세요...")
    print()
    
    try:
        # 웹사이트 크롤링 및 분석
        result = analyzer.crawl_website(url)
        
        # 결과 출력
        formatted_result = formatter.format_analysis_result(result)
        print(formatted_result)
        
        # JSON 저장 (옵션)
        if args.save_json and result.get('success', False):
            filename = args.output if args.output else None
            saved_file = formatter.save_to_json(result, filename)
            print(f"📁 결과가 JSON 파일로 저장되었습니다: {saved_file}")
        
    except Exception as e:
        print(f"❌ 분석 중 오류가 발생했습니다: {str(e)}")


def show_help():
    """도움말 출력"""
    help_text = """
🌐 웹 크롤러 사용법

기본 사용법:
  python main.py --url https://example.com

대화형 모드:
  python main.py --interactive

JSON 저장:
  python main.py --url https://example.com --save-json

옵션:
  --url, -u          분석할 웹사이트 URL
  --interactive, -i  대화형 모드
  --save-json, -s    결과를 JSON으로 저장
  --output, -o       JSON 출력 파일명
  --timeout, -t      요청 타임아웃 (초)
  --help, -h         이 도움말 표시

예시:
  python main.py -u https://news.ycombinator.com
  python main.py -i
  python main.py -u https://example.com -s -o my_result.json
    """
    print(help_text)


if __name__ == "__main__":
    main() 