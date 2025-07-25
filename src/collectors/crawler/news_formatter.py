import json
import csv
import shutil
from typing import Dict, List, Any
from datetime import datetime
import os


class NewsFormatter:
    """뉴스 데이터 포맷팅 및 출력 전용 클래스"""
    
    def __init__(self):
        """NewsFormatter 초기화"""
        self.base_data_dir = "../../data"  # 프로젝트 루트의 data 디렉터리
        
    def _get_today_data_dir(self) -> str:
        """오늘 날짜 기준 데이터 디렉터리 경로를 반환합니다."""
        today = datetime.now().strftime("%Y%m%d")
        return os.path.join(self.base_data_dir, f"ITWorld_{today}")
    
    def _ensure_data_directory(self) -> str:
        """데이터 디렉터리를 생성하고 경로를 반환합니다."""
        data_dir = self._get_today_data_dir()
        
        # 디렉터리가 존재하지 않으면 생성
        os.makedirs(data_dir, exist_ok=True)
        
        return data_dir
    
    def _clean_existing_data(self, file_type: str) -> None:
        """
        지정된 파일 타입의 기존 데이터를 삭제합니다.
        
        Args:
            file_type: 파일 확장자 (json, csv, html)
        """
        data_dir = self._get_today_data_dir()
        
        if not os.path.exists(data_dir):
            return
        
        # 해당 타입의 기존 파일들 찾기
        pattern = f"itworld_news_*.{file_type}"
        existing_files = []
        
        for filename in os.listdir(data_dir):
            if filename.startswith("itworld_news_") and filename.endswith(f".{file_type}"):
                existing_files.append(os.path.join(data_dir, filename))
        
        # 기존 파일들 삭제
        for file_path in existing_files:
            try:
                os.remove(file_path)
                print(f"  🗑️  기존 파일 삭제: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"  ⚠️  파일 삭제 실패: {file_path} - {str(e)}")
    
    def format_news_summary(self, result: Dict[str, Any]) -> str:
        """
        뉴스 크롤링 결과를 요약 형태로 포맷합니다.
        
        Args:
            result: 뉴스 크롤러 결과
            
        Returns:
            포맷된 요약 문자열
        """
        if not result.get('success', False):
            return self._format_error_result(result)
        
        output = []
        output.append("=" * 70)
        output.append("📰 ITWorld 뉴스 크롤링 결과")
        output.append("=" * 70)
        output.append("")
        
        # 기본 정보
        output.append("📋 크롤링 정보")
        output.append("-" * 30)
        output.append(f"출처: {result.get('source', 'Unknown')}")
        output.append(f"URL: {result.get('url', 'N/A')}")
        output.append(f"수집 시간: {result.get('timestamp', 'N/A')}")
        output.append(f"총 뉴스 수: {result.get('total_news', 0)}개")
        
        if result.get('pages_crawled'):
            output.append(f"크롤링한 페이지: {result.get('pages_crawled')}개")
        
        output.append("")
        
        # 카테고리 분포
        categories = result.get('categories', {})
        if categories:
            output.append("📊 카테고리별 분포")
            output.append("-" * 30)
            for category, count in list(categories.items())[:10]:  # 상위 10개만
                output.append(f"  • {category}: {count}개")
            if len(categories) > 10:
                output.append(f"  ... 외 {len(categories) - 10}개 카테고리")
            output.append("")
        
        # 요약 통계
        summary = result.get('summary', {})
        if summary:
            output.append("📈 요약 통계")
            output.append("-" * 30)
            output.append(f"총 기사 수: {summary.get('total_articles', 0)}개")
            output.append(f"이미지 포함 기사: {summary.get('has_images', 0)}개")
            output.append(f"최신 기사 날짜: {summary.get('latest_date', 'N/A')}")
            
            # 세부 내용 수집 통계
            if result.get('content_included'):
                content_count = len([n for n in result.get('news_list', []) if n.get('full_content')])
                total_content_length = sum(n.get('content_length', 0) for n in result.get('news_list', []))
                output.append(f"본문 수집 기사: {content_count}개")
                output.append(f"총 본문 길이: {total_content_length:,}자")
            
            # 컨텐츠 타입 분포
            content_types = summary.get('content_type_distribution', {})
            if content_types:
                output.append("컨텐츠 타입:")
                for content_type, count in content_types.items():
                    output.append(f"  • {content_type}: {count}개")
            output.append("")
        
        # 최신 뉴스 미리보기 (상위 5개)
        news_list = result.get('news_list', [])
        if news_list:
            output.append("📑 최신 뉴스 미리보기 (상위 5개)")
            output.append("-" * 30)
            for i, news in enumerate(news_list[:5]):
                output.append(f"{i+1}. {news.get('title', 'No title')}")
                if news.get('content_type'):
                    output.append(f"   📌 {news.get('content_type')}")
                if news.get('tags'):
                    tags_str = ', '.join(news.get('tags', [])[:3])
                    output.append(f"   🏷️  {tags_str}")
                if news.get('publish_date'):
                    output.append(f"   📅 {news.get('publish_date')}")
                output.append("")
        
        output.append("=" * 70)
        return "\n".join(output)
    
    def format_detailed_news(self, result: Dict[str, Any], max_articles: int = 10) -> str:
        """
        뉴스 리스트를 상세하게 포맷합니다.
        
        Args:
            result: 뉴스 크롤러 결과
            max_articles: 최대 표시할 기사 수
            
        Returns:
            상세 포맷된 뉴스 문자열
        """
        if not result.get('success', False):
            return self._format_error_result(result)
        
        news_list = result.get('news_list', [])
        if not news_list:
            return "📰 수집된 뉴스가 없습니다."
        
        output = []
        output.append("=" * 80)
        output.append(f"📰 ITWorld 뉴스 상세 목록 (상위 {min(max_articles, len(news_list))}개)")
        output.append("=" * 80)
        output.append("")
        
        for i, news in enumerate(news_list[:max_articles]):
            output.append(f"📑 뉴스 #{i+1}")
            output.append("-" * 50)
            output.append(f"제목: {news.get('title', 'No title')}")
            
            if news.get('url'):
                output.append(f"URL: {news.get('url')}")
            
            if news.get('content_type'):
                output.append(f"타입: {news.get('content_type')}")
            
            if news.get('description'):
                desc = news.get('description')
                if len(desc) > 200:
                    desc = desc[:200] + "..."
                output.append(f"설명: {desc}")
            
            if news.get('author'):
                output.append(f"작성자: {news.get('author')}")
            
            if news.get('publish_date'):
                output.append(f"발행일: {news.get('publish_date')}")
            
            if news.get('read_time'):
                output.append(f"읽기 시간: {news.get('read_time')}")
            
            if news.get('tags'):
                tags_str = ', '.join(news.get('tags', []))
                output.append(f"태그: {tags_str}")
            
            if news.get('image_url'):
                output.append(f"이미지: ✅ 포함")
            
            # 본문 내용 (요약)
            if news.get('full_content'):
                content = news.get('full_content', '')
                content_preview = content[:300] + "..." if len(content) > 300 else content
                output.append(f"본문 (처음 300자):\n{content_preview}")
                output.append(f"전체 본문 길이: {len(content):,}자")
            
            output.append(f"수집 시간: {news.get('crawled_at', 'N/A')}")
            output.append("")
        
        if len(news_list) > max_articles:
            output.append(f"... 외 {len(news_list) - max_articles}개 뉴스 더 있음")
        
        output.append("=" * 80)
        return "\n".join(output)
    
    def save_to_json(self, result: Dict[str, Any], filename: str = None) -> str:
        """
        뉴스 데이터를 JSON 파일로 저장합니다.
        
        Args:
            result: 뉴스 크롤러 결과
            filename: 저장할 파일명 (None이면 자동 생성)
            
        Returns:
            저장된 파일 경로
        """
        # 데이터 디렉터리 생성
        data_dir = self._ensure_data_directory()
        
        # 기존 JSON 파일들 삭제
        self._clean_existing_data("json")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"itworld_news_{timestamp}.json"
        
        file_path = os.path.join(data_dir, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return file_path
    
    def save_to_csv(self, result: Dict[str, Any], filename: str = None) -> str:
        """
        뉴스 데이터를 CSV 파일로 저장합니다.
        
        Args:
            result: 뉴스 크롤러 결과
            filename: 저장할 파일명 (None이면 자동 생성)
            
        Returns:
            저장된 파일 경로
        """
        news_list = result.get('news_list', [])
        if not news_list:
            return None
        
        # 데이터 디렉터리 생성
        data_dir = self._ensure_data_directory()
        
        # 기존 CSV 파일들 삭제
        self._clean_existing_data("csv")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"itworld_news_{timestamp}.csv"
        
        file_path = os.path.join(data_dir, filename)
        
        # CSV 헤더 정의
        fieldnames = [
            'title', 'url', 'content_type', 'description', 'author', 
            'publish_date', 'read_time', 'tags', 'image_url', 
            'image_alt', 'full_content', 'content_length', 'crawled_at', 'source'
        ]
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for news in news_list:
                # 태그를 문자열로 변환
                row = news.copy()
                if isinstance(row.get('tags'), list):
                    row['tags'] = ', '.join(row['tags'])
                
                # 필드명에 맞춰서만 저장
                filtered_row = {k: v for k, v in row.items() if k in fieldnames}
                writer.writerow(filtered_row)
        
        return file_path
    
    def create_html_report(self, result: Dict[str, Any], filename: str = None) -> str:
        """
        뉴스 데이터를 HTML 보고서로 생성합니다.
        
        Args:
            result: 뉴스 크롤러 결과
            filename: 저장할 파일명 (None이면 자동 생성)
            
        Returns:
            저장된 파일 경로
        """
        # 데이터 디렉터리 생성
        data_dir = self._ensure_data_directory()
        
        # 기존 HTML 파일들 삭제
        self._clean_existing_data("html")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"itworld_news_report_{timestamp}.html"
        
        file_path = os.path.join(data_dir, filename)
        
        news_list = result.get('news_list', [])
        categories = result.get('categories', {})
        summary = result.get('summary', {})
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ITWorld 뉴스 크롤링 보고서 - {datetime.now().strftime('%Y-%m-%d')}</title>
            <style>
                body {{ font-family: 'Malgun Gothic', Arial, sans-serif; margin: 40px; line-height: 1.6; background-color: #f8f9fa; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; text-align: center; }}
                .summary {{ background: #ffffff; padding: 20px; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .news-item {{ border: 1px solid #ddd; margin-bottom: 20px; padding: 20px; border-radius: 8px; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
                .news-title {{ font-size: 1.3em; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }}
                .news-meta {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 10px; }}
                .news-description {{ margin-bottom: 10px; color: #34495e; }}
                .news-content {{ margin-top: 15px; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
                .tags {{ margin-top: 10px; }}
                .tag {{ background: #3498db; color: white; padding: 3px 8px; border-radius: 3px; font-size: 0.8em; margin-right: 5px; }}
                .stats {{ display: flex; justify-content: space-between; margin-bottom: 20px; flex-wrap: wrap; }}
                .stat-box {{ background: white; border: 1px solid #ddd; padding: 15px; border-radius: 8px; text-align: center; flex: 1; margin: 5px; min-width: 150px; }}
                .stat-number {{ font-size: 2em; font-weight: bold; color: #2c3e50; }}
                .stat-label {{ color: #7f8c8d; font-size: 0.9em; }}
                a {{ color: #3498db; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                .content-toggle {{ cursor: pointer; color: #3498db; font-size: 0.9em; margin-top: 10px; }}
                .content-toggle:hover {{ text-decoration: underline; }}
                .full-content {{ display: none; max-height: 300px; overflow-y: auto; }}
            </style>
            <script>
                function toggleContent(id) {{
                    var content = document.getElementById('content-' + id);
                    var toggle = document.getElementById('toggle-' + id);
                    if (content.style.display === 'none') {{
                        content.style.display = 'block';
                        toggle.textContent = '본문 접기';
                    }} else {{
                        content.style.display = 'none';
                        toggle.textContent = '본문 전체 보기';
                    }}
                }}
            </script>
        </head>
        <body>
            <div class="header">
                <h1>📰 ITWorld 뉴스 크롤링 보고서</h1>
                <p>수집 날짜: {result.get('timestamp', 'N/A')}</p>
                <p>출처: {result.get('source', 'N/A')}</p>
                <p>저장 위치: {data_dir}</p>
            </div>
            
            <div class="summary">
                <h2>📊 수집 요약</h2>
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-number">{result.get('total_news', 0)}</div>
                        <div class="stat-label">총 뉴스 수</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">{summary.get('has_images', 0)}</div>
                        <div class="stat-label">이미지 포함</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">{len(categories)}</div>
                        <div class="stat-label">카테고리 수</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">{summary.get('latest_date', 'N/A')}</div>
                        <div class="stat-label">최신 날짜</div>
                    </div>
        """
        
        # 본문 수집 통계 추가
        if result.get('content_included'):
            content_count = len([n for n in news_list if n.get('full_content')])
            total_length = sum(n.get('content_length', 0) for n in news_list)
            html_content += f"""
                    <div class="stat-box">
                        <div class="stat-number">{content_count}</div>
                        <div class="stat-label">본문 수집</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">{total_length:,}</div>
                        <div class="stat-label">총 본문 길이</div>
                    </div>
            """
        
        html_content += """
                </div>
        """
        
        # 상위 카테고리
        if categories:
            html_content += "<h3>🏷️ 주요 카테고리</h3><p>"
            for cat, count in list(categories.items())[:10]:
                html_content += f"<span class='tag'>{cat} ({count})</span>"
            html_content += "</p>"
        
        html_content += "</div>"
        
        # 뉴스 목록
        html_content += "<h2>📑 뉴스 목록</h2>"
        
        for i, news in enumerate(news_list):
            title = news.get('title', 'No title')
            url = news.get('url', '#')
            description = news.get('description', '')
            content_type = news.get('content_type', '')
            author = news.get('author', '')
            publish_date = news.get('publish_date', '')
            tags = news.get('tags', [])
            full_content = news.get('full_content', '')
            content_length = news.get('content_length', 0)
            
            html_content += f"""
            <div class="news-item">
                <div class="news-title">
                    <a href="{url}" target="_blank">{title}</a>
                </div>
                <div class="news-meta">
                    {content_type} | {publish_date} | {author}
            """
            
            if content_length > 0:
                html_content += f" | 본문 {content_length:,}자"
            
            html_content += f"""
                </div>
                <div class="news-description">{description}</div>
                <div class="tags">
            """
            
            for tag in tags:
                html_content += f"<span class='tag'>{tag}</span>"
            
            # 본문 내용이 있으면 토글 기능 추가
            if full_content:
                preview = full_content[:200] + "..." if len(full_content) > 200 else full_content
                html_content += f"""
                </div>
                <div class="news-content">
                    <strong>본문 미리보기:</strong><br>
                    {preview}
                    <div class="content-toggle" id="toggle-{i}" onclick="toggleContent({i})">본문 전체 보기</div>
                    <div class="full-content" id="content-{i}">
                        <hr>
                        <strong>전체 본문:</strong><br>
                        {full_content.replace(chr(10), '<br>')}
                    </div>
                </div>
                """
            else:
                html_content += "</div>"
            
            html_content += "</div>"
        
        html_content += """
        </body>
        </html>
        """
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return file_path
    
    def _format_error_result(self, result: Dict[str, Any]) -> str:
        """오류 결과를 포맷합니다."""
        output = []
        output.append("=" * 70)
        output.append("❌ 뉴스 크롤링 실패")
        output.append("=" * 70)
        output.append("")
        output.append(f"오류: {result.get('error', 'Unknown error')}")
        output.append(f"시간: {result.get('timestamp', 'N/A')}")
        output.append("")
        output.append("해결 방법:")
        output.append("  • 네트워크 연결을 확인해주세요")
        output.append("  • 웹사이트가 접근 가능한지 확인해주세요")
        output.append("  • 잠시 후 다시 시도해주세요")
        output.append("=" * 70)
        
        return "\n".join(output) 
        return "\n".join(output) 