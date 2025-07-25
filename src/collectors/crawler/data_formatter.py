import json
from typing import Dict, Any, List
from datetime import datetime


class DataFormatter:
    """크롤링 결과를 포맷하고 출력하는 클래스"""
    
    def __init__(self):
        """DataFormatter 초기화"""
        pass
    
    def format_analysis_result(self, result: Dict[str, Any]) -> str:
        """
        분석 결과를 사용자가 읽기 쉬운 형태로 포맷합니다.
        
        Args:
            result: WebAnalyzer에서 반환된 분석 결과
            
        Returns:
            포맷된 분석 결과 문자열
        """
        if not result.get('success', False):
            return self._format_error_result(result)
        
        output = []
        output.append("=" * 60)
        output.append("🌐 웹사이트 크롤링 분석 결과")
        output.append("=" * 60)
        output.append("")
        
        # 기본 정보
        output.append("📋 기본 정보")
        output.append("-" * 20)
        output.append(f"URL: {result['url']}")
        output.append(f"상태 코드: {result['status_code']}")
        output.append(f"분석 시간: {result['timestamp']}")
        output.append("")
        
        # 웹사이트 정보
        basic_info = result.get('basic_info', {})
        output.append("📰 웹사이트 정보")
        output.append("-" * 20)
        output.append(f"제목: {basic_info.get('title', 'N/A')}")
        output.append(f"설명: {basic_info.get('description', 'N/A')}")
        output.append(f"키워드: {basic_info.get('keywords', 'N/A')}")
        output.append("")
        
        # 콘텐츠 분석
        content_analysis = result.get('content_analysis', {})
        output.append("📊 콘텐츠 분석")
        output.append("-" * 20)
        
        text_stats = content_analysis.get('text_stats', {})
        output.append(f"총 단어 수: {text_stats.get('total_words', 0):,}")
        output.append(f"고유 단어 수: {text_stats.get('unique_words', 0):,}")
        
        common_words = text_stats.get('most_common_words', [])
        if common_words:
            output.append("자주 사용되는 단어:")
            for word, count in common_words[:5]:
                output.append(f"  • {word}: {count}회")
        
        media_stats = content_analysis.get('media_stats', {})
        output.append(f"이미지 수: {media_stats.get('total_images', 0)}")
        output.append(f"Alt 텍스트가 있는 이미지: {media_stats.get('images_with_alt', 0)}")
        
        link_stats = content_analysis.get('link_stats', {})
        output.append(f"총 링크 수: {link_stats.get('total_links', 0)}")
        output.append(f"내부 링크: {link_stats.get('internal_links', 0)}")
        output.append(f"외부 링크: {link_stats.get('external_links', 0)}")
        output.append("")
        
        # 구조 분석
        structure_analysis = result.get('structure_analysis', {})
        output.append("🏗️ HTML 구조 분석")
        output.append("-" * 20)
        
        structural_elements = structure_analysis.get('structural_elements', {})
        output.append(f"테이블: {structural_elements.get('tables', 0)}개")
        output.append(f"폼: {structural_elements.get('forms', 0)}개")
        output.append(f"리스트: {structural_elements.get('lists', 0)}개")
        output.append(f"제목 태그: {structural_elements.get('headings', 0)}개")
        output.append(f"문단: {structural_elements.get('paragraphs', 0)}개")
        
        tag_distribution = structure_analysis.get('tag_distribution', {})
        if tag_distribution:
            output.append("주요 HTML 태그 분포:")
            for tag, count in list(tag_distribution.items())[:8]:
                output.append(f"  • <{tag}>: {count}개")
        output.append("")
        
        # 데이터 수집 기회
        data_opportunities = result.get('data_opportunities', {})
        output.append("💎 데이터 수집 기회")
        output.append("-" * 20)
        output.append(f"총 기회: {data_opportunities.get('total_opportunities', 0)}개")
        
        opportunities = data_opportunities.get('opportunities', [])
        if opportunities:
            output.append("발견된 데이터 패턴:")
            for opp in opportunities:
                icon = self._get_opportunity_icon(opp['type'])
                output.append(f"  {icon} {opp['description']}")
                output.append(f"     → {opp['potential_data']}")
        
        recommendations = data_opportunities.get('recommendations', [])
        if recommendations:
            output.append("")
            output.append("🔍 추천사항:")
            for rec in recommendations:
                output.append(f"  {rec}")
        
        output.append("")
        output.append("=" * 60)
        
        return "\n".join(output)
    
    def _format_error_result(self, result: Dict[str, Any]) -> str:
        """오류 결과를 포맷합니다."""
        output = []
        output.append("=" * 60)
        output.append("❌ 크롤링 실패")
        output.append("=" * 60)
        output.append("")
        output.append(f"URL: {result.get('url', 'N/A')}")
        output.append(f"오류: {result.get('error', 'Unknown error')}")
        output.append(f"시간: {result.get('timestamp', 'N/A')}")
        output.append("")
        output.append("해결 방법:")
        output.append("  • URL이 올바른지 확인해주세요")
        output.append("  • 인터넷 연결을 확인해주세요")
        output.append("  • 웹사이트가 접근 가능한지 확인해주세요")
        output.append("=" * 60)
        
        return "\n".join(output)
    
    def _get_opportunity_icon(self, opportunity_type: str) -> str:
        """기회 타입에 따른 아이콘을 반환합니다."""
        icons = {
            'table': '📊',
            'list': '📝',
            'repeated_pattern': '🔄',
            'form': '📋'
        }
        return icons.get(opportunity_type, '📌')
    
    def to_json(self, result: Dict[str, Any], pretty: bool = True) -> str:
        """
        분석 결과를 JSON 형태로 변환합니다.
        
        Args:
            result: 분석 결과
            pretty: JSON을 예쁘게 포맷할지 여부
            
        Returns:
            JSON 문자열
        """
        if pretty:
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            return json.dumps(result, ensure_ascii=False)
    
    def save_to_json(self, result: Dict[str, Any], filename: str = None) -> str:
        """
        분석 결과를 JSON 파일로 저장합니다.
        
        Args:
            result: 분석 결과
            filename: 저장할 파일명 (None이면 자동 생성)
            
        Returns:
            저장된 파일 경로
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            url_safe = result.get('url', 'unknown').replace('://', '_').replace('/', '_')
            filename = f"crawl_result_{url_safe}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return filename 