import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, List
import json

class ElectronicsIPCrawler:
    """전자 분야 특허 및 IP 데이터 크롤링 클래스"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # 주요 전자업체 리스트
        self.major_electronics_companies = [
            'Samsung', 'Apple', 'Sony', 'LG Electronics', 'Intel', 
            'Qualcomm', 'NVIDIA', 'AMD', 'Broadcom', 'MediaTek',
            'TSMC', 'SK Hynix', 'Micron', 'Texas Instruments'
        ]
        
        # 전자 분야 IPC 분류
        self.electronics_ipc = {
            'H01': '기본적 전기 소자',
            'H02': '전력의 발생, 변환, 배전', 
            'H03': '기본적 전자회로',
            'H04': '전기통신기술',
            'H05': '달리 분류되지 않는 전기기술',
            'G06': '컴퓨팅, 계산, 계수',
            'G11': '정보저장',
            'G02': '광학',
            'G01': '측정, 시험'
        }

    def search_uspto_patents(self, query: str, limit: int = 100) -> List[Dict]:
        """USPTO API를 통한 특허 검색"""
        base_url = "https://developer.uspto.gov/ibd/api/v1/application/publications"
        
        params = {
            'searchText': query,
            'start': '2020-01-01',
            'rows': limit
        }
        
        try:
            response = requests.get(base_url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data.get('response', {}).get('docs', [])
        except Exception as e:
            print(f"USPTO 검색 오류: {e}")
            return []

    def search_google_patents(self, query: str, country: str = "US") -> List[Dict]:
        """Google Patents API 검색"""
        # 실제 구현시 Google Patents Public Datasets BigQuery 사용 권장
        url = "https://serpapi.com/search"  # 예시용 (실제로는 공식 API 사용)
        
        params = {
            'engine': 'google_patents',
            'q': query,
            'country': country,
            'num': 50
        }
        
        # API 키가 필요한 경우의 예시
        return []

    def crawl_company_patents(self, company: str, technology: str = "electronics") -> Dict:
        """특정 회사의 전자 분야 특허 크롤링"""
        query = f'assignee:"{company}" AND {technology}'
        patents = self.search_uspto_patents(query)
        
        result = {
            'company': company,
            'total_patents': len(patents),
            'patents': patents,
            'crawl_date': datetime.now().isoformat()
        }
        
        return result

    def monitor_ipc_trends(self, ipc_codes: List[str], date_range: int = 365) -> Dict:
        """IPC 코드별 특허 트렌드 모니터링"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=date_range)
        
        trends = {}
        
        for ipc_code in ipc_codes:
            query = f'ipc:{ipc_code}*'
            patents = self.search_uspto_patents(query)
            
            trends[ipc_code] = {
                'description': self.electronics_ipc.get(ipc_code, 'Unknown'),
                'patent_count': len(patents),
                'patents': patents[:10]  # 상위 10개만 저장
            }
            
            time.sleep(1)  # Rate limiting
        
        return trends

    def analyze_technology_keywords(self, patents: List[Dict]) -> Dict:
        """특허 데이터에서 기술 키워드 분석"""
        keywords = {}
        tech_keywords = [
            'AI', 'artificial intelligence', 'machine learning',
            'semiconductor', '5G', '6G', 'IoT', 'blockchain',
            'quantum', 'neural network', 'deep learning',
            'OLED', 'battery', 'processor', 'chip', 'sensor'
        ]
        
        for patent in patents:
            title = patent.get('title', '').lower()
            abstract = patent.get('abstract', '').lower()
            
            for keyword in tech_keywords:
                if keyword.lower() in title or keyword.lower() in abstract:
                    keywords[keyword] = keywords.get(keyword, 0) + 1
        
        return sorted(keywords.items(), key=lambda x: x[1], reverse=True)

    def export_to_csv(self, data: Dict, filename: str):
        """데이터를 CSV 파일로 내보내기"""
        if 'patents' in data:
            df = pd.DataFrame(data['patents'])
            df.to_csv(f"{filename}_{datetime.now().strftime('%Y%m%d')}.csv", 
                     index=False, encoding='utf-8-sig')
            print(f"데이터가 {filename}_{datetime.now().strftime('%Y%m%d')}.csv로 저장되었습니다.")

    def comprehensive_electronics_report(self) -> Dict:
        """전자 분야 종합 IP 리포트 생성"""
        report = {
            'generation_date': datetime.now().isoformat(),
            'company_analysis': {},
            'ipc_trends': {},
            'technology_keywords': {}
        }
        
        # 주요 회사별 특허 분석
        for company in self.major_electronics_companies[:5]:  # 상위 5개사만
            print(f"분석 중: {company}")
            company_data = self.crawl_company_patents(company)
            report['company_analysis'][company] = company_data
            time.sleep(2)  # Rate limiting
        
        # IPC 트렌드 분석
        main_ipc_codes = ['H01', 'H04', 'G06']
        report['ipc_trends'] = self.monitor_ipc_trends(main_ipc_codes)
        
        return report

# 사용 예시
def main():
    crawler = ElectronicsIPCrawler()
    
    # 1. 특정 회사 특허 크롤링
    samsung_patents = crawler.crawl_company_patents("Samsung", "semiconductor")
    print(f"삼성 반도체 특허: {samsung_patents['total_patents']}건")
    
    # 2. IPC 코드별 트렌드 분석
    ipc_trends = crawler.monitor_ipc_trends(['H01', 'H04'])
    for ipc, data in ipc_trends.items():
        print(f"{ipc} ({data['description']}): {data['patent_count']}건")
    
    # 3. 종합 리포트 생성
    # report = crawler.comprehensive_electronics_report()
    
    # 4. 데이터 내보내기
    # crawler.export_to_csv(samsung_patents, "samsung_patents")

if __name__ == "__main__":
    main()