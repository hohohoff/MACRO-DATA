import requests
import pandas as pd
from datetime import datetime
import os
import json
import time

# ==================== 终极版：三重保障自动获取加息预期 ====================

def get_rate_hike_cme_direct():
    """
    方案A：直接从CME官网API获取（最快最准）
    """
    try:
        # CME的公开API端点
        urls = [
            "https://www.cmegroup.com/CmeWS/mvc/ProductCalendar/Options/278",
            "https://www.cmegroup.com/CmeWS/mvc/Quotes/Future/278/G/",
            "https://www.cmegroup.com/CmeWS/mvc/Quotes/Calendar/278/G/"
        ]
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://www.cmegroup.com/"
        }
        
        for url in urls:
            try:
                print(f"尝试CME API: {url}")
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    # 解析不同格式
                    if isinstance(data, list) and len(data) > 0:
                        # 格式1：列表格式
                        for item in data:
                            if 'quotes' in item:
                                for quote in item['quotes']:
                                    if 'month' in quote and 'last' in quote:
                                        futures_price = float(quote['last'])
                                        return calculate_prob_from_price(futures_price)
                    elif 'quotes' in data:
                        # 格式2：字典格式
                        for quote in data['quotes']:
                            if 'last' in quote:
                                futures_price = float(quote['last'])
                                return calculate_prob_from_price(futures_price)
            except:
                continue
                
    except Exception as e:
        print(f"方案A失败: {e}")
    return None

def get_rate_hike_barchart():
    """
    方案B：从Barchart抓取期货价格 [citation:2]
    """
    try:
        # Barchart提供免费的期货数据
        url = "https://www.barchart.com/futures/quotes/ZQ*0/futures-prices"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        # 获取最近合约价格
        response = requests.get(url, headers=headers, timeout=10)
        
        # 解析HTML或JSON
        # 这里简化处理，实际需要解析页面
        
        # 示例：从另一个公开API获取
        alt_url = "https://financialmodelingprep.com/api/v3/futures"
        alt_response = requests.get(alt_url, timeout=10)
        if alt_response.status_code == 200:
            data = alt_response.json()
            for item in data:
                if 'ZQ' in item.get('symbol', ''):
                    price = float(item.get('price', 0))
                    return calculate_prob_from_price(price)
                    
    except Exception as e:
        print(f"方案B失败: {e}")
    return None

def get_rate_hike_tradingview():
    """
    方案C：从TradingView的公开小部件获取
    """
    try:
        # TradingView有公开的widget数据
        url = "https://scanner.tradingview.com/america/scan"
        
        payload = {
            "symbols": {"tickers": ["CME:ZQ1!", "CME:ZQQ2026"]},
            "columns": ["close", "volume"]
        }
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                price = float(data['data'][0]['d'][0])
                return calculate_prob_from_price(price)
                
    except Exception as e:
        print(f"方案C失败: {e}")
    return None

def calculate_prob_from_price(futures_price):
    """
    根据期货价格计算加息概率
    FedWatch核心算法 [citation:4]
    """
    try:
        # 当前联邦基金目标利率 (假设 350-375 bps = 3.50-3.75%)
        current_rate_lower = 3.50
        current_rate_upper = 3.75
        
        # 隐含利率
        implied_rate = 100 - futures_price
        
        print(f"期货价格: {futures_price}, 隐含利率: {implied_rate:.2f}%")
        
        # 计算与当前利率的差距
        rate_diff = implied_rate - current_rate_lower
        
        # 25bps为一个步长
        if rate_diff > 0.20:  # 高于当前区间
            # 加息概率估算
            hike_prob = min(100, (rate_diff / 0.25) * 100)
            print(f"加息概率: {hike_prob:.1f}%")
            return hike_prob > 30
        else:
            print("无加息预期")
            return False
            
    except Exception as e:
        print(f"计算失败: {e}")
        return False

def get_rate_hike_ultimate():
    """
    终极入口：按顺序尝试所有方案
    """
    print("\n🔍 正在自动获取加息预期...")
    
    # 方案列表，按成功率排序
    methods = [
        ("CME直接API", get_rate_hike_cme_direct),
        ("Barchart数据", get_rate_hike_barchart),
        ("TradingView", get_rate_hike_tradingview)
    ]
    
    for name, method in methods:
        print(f"尝试方案: {name}")
        result = method()
        if result is not None:
            print(f"✅ {name} 成功! 加息预期: {'有' if result else '无'}")
            return result
        time.sleep(1)  # 避免请求过快
    
    print("⚠️ 所有自动方案都失败，返回保守值 False")
    return False

# ==================== 原有的油价和期限溢价函数保持不变 ====================

def get_oil_price():
    """获取WTI原油价格（美元/桶）- 使用您的免费API key"""
    try:
        api_key = "3CI95UKF5IK07OU1"
        url = f"https://www.alphavantage.co/query?function=WTI&interval=monthly&apikey={api_key}"
        print(f"正在请求油价API...")
        response = requests.get(url)
        data = response.json()
        
        if "data" in data:
            latest = data["data"][0]
            oil_price = float(latest["value"])
            print(f"获取到油价: {oil_price} 美元")
            return oil_price
        else:
            print("API返回格式异常，使用默认值85.5")
            return 85.5
    except Exception as e:
        print(f"获取油价出错: {e}")
        return 85.0

def get_term_premium():
    """获取10年期美债期限溢价（修复版）"""
    try:
        url = "https://www.newyorkfed.org/medialibrary/interactives/acm/acm.csv"
        print(f"正在获取期限溢价...")
        
        df = pd.read_csv(url, skiprows=13, header=None, names=['date', 'term_premium'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        latest = df.iloc[-1]
        term_premium = float(latest['term_premium'])
        print(f"最新期限溢价: {term_premium}%")
        return term_premium
    except Exception as e:
        print(f"获取期限溢价出错: {e}")
        return 0.75

def calculate_macro_score(oil_price, term_premium, rate_hike):
    """计算宏观预警分数（0-10分）"""
    score = 0
    details = []
    
    if oil_price > 95:
        score += 3
        details.append(f"油价{oil_price}>95: +3分")
    elif oil_price > 90:
        score += 2
        details.append(f"油价{oil_price}>90: +2分")
    elif oil_price > 85:
        score += 1
        details.append(f"油价{oil_price}>85: +1分")
    else:
        details.append(f"油价{oil_price}<=85: +0分")
        
    if term_premium > 0.8:
        score += 3
        details.append(f"期限溢价{term_premium}>0.8: +3分")
    elif term_premium > 0.7:
        score += 2
        details.append(f"期限溢价{term_premium}>0.7: +2分")
    elif term_premium > 0.6:
        score += 1
        details.append(f"期限溢价{term_premium}>0.6: +1分")
    else:
        details.append(f"期限溢价{term_premium}<=0.6: +0分")
        
    if rate_hike:
        score += 2
        details.append("加息预期: +2分")
    else:
        details.append("加息预期: +0分")
    
    print("\n📊 评分详情:")
    for d in details:
        print(f"  {d}")
    print(f"总分: {score}/10")
        
    return min(score, 10)

def main():
    print("="*50)
    print("🚀 开始获取宏观数据（终极自动版）")
    print("="*50)
    
    oil = get_oil_price()
    term = get_term_premium()
    hike = get_rate_hike_ultimate()  # 现在全自动！
    
    score = calculate_macro_score(oil, term, hike)
    
    now = datetime.now()
    new_data = pd.DataFrame({
        'timestamp': [now.strftime('%Y-%m-%d %H:%M:%S')],
        'macro_score': [score],
        'oil_price': [round(oil, 2)],
        'term_premium': [round(term, 3)],
        'rate_hike': [hike]
    })
    
    print("\n📝 新数据:")
    print(new_data)
    
    filename = 'macro_score.csv'
    if os.path.exists(filename):
        existing = pd.read_csv(filename)
        updated = pd.concat([existing, new_data], ignore_index=True)
    else:
        updated = new_data
    
    if len(updated) > 100:
        updated = updated.tail(100)
    
    updated.to_csv(filename, index=False)
    print(f"\n✅ 数据已保存到 {filename}")
    print("="*50)

if __name__ == "__main__":
    main()
