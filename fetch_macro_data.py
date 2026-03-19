import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import yfinance as yf
import pyfedwatch as fw

def get_oil_price():
    """获取WTI原油价格（美元/桶）"""
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
        
        # 正确解析NY Fed的CSV格式
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

def get_rate_hike_expect_auto():
    """
    全自动获取加息预期！使用 yfinance + pyfedwatch
    yfinance 免费获取联邦基金期货数据 [citation:4]
    pyfedwatch 实现CME FedWatch算法 [citation:9]
    """
    try:
        print("\n🔍 正在自动计算加息预期...")
        
        # 1. 从Yahoo Finance获取联邦基金期货价格 [citation:10]
        # 代码：ZQ=F (30-Day Fed Funds Futures)
        futures = yf.Ticker("ZQ=F")
        
        # 获取未来几个月的期货价格
        # 需要获取不同合约月的价格，这里简化处理，用当前合约
        hist = futures.history(period="5d")
        current_price = hist['Close'].iloc[-1]
        
        # 计算隐含利率：100 - 期货价格 [citation:5]
        implied_rate = 100 - current_price
        print(f"当前期货价格: {current_price:.2f}")
        print(f"隐含利率: {implied_rate:.2f}%")
        
        # 2. 准备FOMC会议日期（2026年）[citation:9]
        fomc_dates = [
            '2026-01-28', '2026-03-18', '2026-04-29', 
            '2026-06-10', '2026-07-29', '2026-09-16',
            '2026-10-28', '2026-12-09'
        ]
        
        # 3. 定义读取价格历史的函数（pyfedwatch需要）[citation:1]
        def read_price_history(contract_month, path=None):
            """返回指定合约月的期货价格"""
            # 这里简化处理：用当前价格近似
            # 实际应该根据contract_month获取对应合约的价格
            return implied_rate
        
        # 4. 使用pyfedwatch计算概率 [citation:9]
        fedwatch = fw.fedwatch.FedWatch(
            watch_date=datetime.now().strftime('%Y-%m-%d'),
            fomc_dates=fomc_dates,
            num_upcoming=5,
            user_func=read_price_history
        )
        
        probabilities = fedwatch.generate_hike_info()
        
        # 提取最近会议的加息概率
        # probabilities是一个DataFrame，第一行是最近会议
        latest_probs = probabilities.iloc[0]
        hike_prob = latest_probs.get('P_Hike', 0) * 100
        
        print(f"📊 计算出的加息概率: {hike_prob:.1f}%")
        
        # 判断是否有加息预期（>30%）
        has_hike_expect = hike_prob > 30
        print(f"加息预期: {'有 ✅' if has_hike_expect else '无 ❌'}")
        
        return has_hike_expect
        
    except Exception as e:
        print(f"自动获取加息预期出错: {e}")
        print("⚠️ 使用保守默认值：无加息预期")
        return False  # 出错时保守返回False

def calculate_macro_score(oil_price, term_premium, rate_hike):
    """计算宏观预警分数（0-10分）"""
    score = 0
    details = []
    
    # 油价评分
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
        
    # 期限溢价评分
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
        
    # 加息预期评分
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
    print("🚀 开始获取宏观数据（全自动版）")
    print("="*50)
    
    # 获取数据
    oil = get_oil_price()
    term = get_term_premium()
    hike = get_rate_hike_expect_auto()  # 现在全自动了！
    
    # 计算分数
    score = calculate_macro_score(oil, term, hike)
    
    # 创建新数据行
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
    
    # 读取现有文件或创建新文件
    filename = 'macro_score.csv'
    if os.path.exists(filename):
        print(f"\n📂 读取现有文件 {filename}")
        existing = pd.read_csv(filename)
        print(f"现有数据 {len(existing)} 条")
        updated = pd.concat([existing, new_data], ignore_index=True)
    else:
        print(f"\n📂 创建新文件 {filename}")
        updated = new_data
    
    # 只保留最近100条记录
    if len(updated) > 100:
        updated = updated.tail(100)
        print(f"保留最近100条记录")
    
    # 保存文件
    updated.to_csv(filename, index=False)
    print(f"\n✅ 数据已保存到 {filename}")
    print(f"现在共有 {len(updated)} 条记录")
    print("="*50)

if __name__ == "__main__":
    main()
