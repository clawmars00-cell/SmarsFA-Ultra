"""
综合评分系统 - Comprehensive Scoring System
=============================================
整合四个维度:
1. 财务评分 (Financial Score) - 财报、估值、增长
2. 技术评分 (Technical Score) - 趋势、动量、支撑阻力
3. 舆情评分 (Sentiment Score) - 新闻、社交媒体情绪
4. 宏观政治评分 (Macro-Political Score) - 宏观经济+政治事件影响

最终输出: 综合评分 (0-100) + 投资建议
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import re
import requests
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')


class ComprehensiveScoringSystem:
    """
    综合评分系统 - 四维度评分 + 综合建议
    """
    
    def __init__(self):
        # 权重配置
        self.weights = {
            'financial': 0.35,      # 财务35%
            'technical': 0.25,     # 技术25%
            'sentiment': 0.20,      # 舆情20%
            'macro_political': 0.20 # 宏观政治20%
        }
        
        # 评分阈值
        self.thresholds = {
            'strong_buy': 75,
            'buy': 60,
            'hold': 45,
            'sell': 30
        }
        
        # 行业宏观敏感度映射
        self.industry_macro_sensitivity = {
            # 行业: {宏观因子权重}
            'tech': {'interest_rate': 0.3, 'inflation': 0.2, 'gdp': 0.3, 'dollar': 0.2},
            'finance': {'interest_rate': 0.4, 'inflation': 0.2, 'gdp': 0.3, 'dollar': 0.1},
            'energy': {'inflation': 0.3, 'interest_rate': 0.2, 'geopolitics': 0.4, 'dollar': 0.1},
            'healthcare': {'inflation': 0.2, 'regulation': 0.4, 'gdp': 0.2, 'demographic': 0.2},
            'consumer': {'inflation': 0.3, 'gdp': 0.3, 'employment': 0.2, 'consumer_confidence': 0.2},
            'industrial': {'gdp': 0.4, 'interest_rate': 0.2, 'inflation': 0.2, 'trade': 0.2},
            'real_estate': {'interest_rate': 0.5, 'gdp': 0.2, 'inflation': 0.2, 'regulation': 0.1},
            'utilities': {'interest_rate': 0.4, 'inflation': 0.3, 'regulation': 0.2, 'gdp': 0.1},
        }
        
    def analyze(self, symbol: str, sector: str = 'tech') -> Dict:
        """
        综合分析一只股票
        
        Args:
            symbol: 股票代码
            sector: 行业 (用于宏观敏感度)
            
        Returns:
            完整分析报告
        """
        result = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'sector': sector,
            'scores': {},
            'recommendation': {},
            'details': {}
        }
        
        # 1. 财务评分
        print(f"📊 分析 {symbol} 财务数据...")
        financial_score, financial_details = self._financial_score(symbol)
        result['scores']['financial'] = financial_score
        result['details']['financial'] = financial_details
        
        # 2. 技术评分
        print(f"📈 分析 {symbol} 技术指标...")
        technical_score, technical_details = self._technical_score(symbol)
        result['scores']['technical'] = technical_score
        result['details']['technical'] = technical_details
        
        # 3. 舆情评分
        print(f"📰 分析 {symbol} 舆情...")
        sentiment_score, sentiment_details = self._sentiment_score(symbol)
        result['scores']['sentiment'] = sentiment_score
        result['details']['sentiment'] = sentiment_details
        
        # 4. 宏观政治评分
        print(f"🌍 分析宏观政治影响...")
        macro_score, macro_details = self._macro_political_score(sector)
        result['scores']['macro_political'] = macro_score
        result['details']['macro_political'] = macro_details
        
        # 计算综合评分
        overall = (
            result['scores']['financial'] * self.weights['financial'] +
            result['scores']['technical'] * self.weights['technical'] +
            result['scores']['sentiment'] * self.weights['sentiment'] +
            result['scores']['macro_political'] * self.weights['macro_political']
        )
        
        result['overall_score'] = round(overall, 1)
        result['recommendation'] = self._generate_recommendation(overall)
        
        return result
    
    # ==================== 财务评分 ====================
    def _financial_score(self, symbol: str) -> Tuple[float, Dict]:
        """
        财务评分 (0-100)
        评估: 盈利能力、成长性、估值、现金流、资产负债表
        """
        details = {}
        scores = []
        
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            # 1. 盈利能力 (25分)
            profit_score = 0
            if info.get('profitMargins') and info['profitMargins'] > 0.15:
                profit_score = 25
            elif info.get('profitMargins') and info['profitMargins'] > 0.1:
                profit_score = 20
            elif info.get('profitMargins') and info['profitMargins'] > 0.05:
                profit_score = 15
            elif info.get('profitMargins') and info['profitMargins'] > 0:
                profit_score = 10
            scores.append(profit_score)
            details['profitability'] = profit_score
            
            # 2. 成长性 (25分)
            growth_score = 0
            rev_growth = info.get('revenueGrowth', 0) or 0
            earnings_growth = info.get('earningsGrowth', 0) or 0
            
            if rev_growth > 0.2 and earnings_growth > 0.15:
                growth_score = 25
            elif rev_growth > 0.1 and earnings_growth > 0.08:
                growth_score = 20
            elif rev_growth > 0.05 and earnings_growth > 0.03:
                growth_score = 15
            elif rev_growth > 0:
                growth_score = 10
            scores.append(growth_score)
            details['growth'] = growth_score
            
            # 3. 估值 (25分)
            valuation_score = 0
            pe = info.get('forwardPE') or info.get('trailingPE')
            peg = info.get('pegRatio')
            
            if pe and peg:
                if pe < 20 and peg < 1:
                    valuation_score = 25
                elif pe < 25 and peg < 1.5:
                    valuation_score = 20
                elif pe < 30 and peg < 2:
                    valuation_score = 15
                elif pe < 40:
                    valuation_score = 10
            scores.append(valuation_score)
            details['valuation'] = valuation_score
            
            # 4. 现金流 (15分)
            fcf_score = 0
            fcf = info.get('freeCashflow')
            if fcf and fcf > 0:
                if fcf > 1e10:  # >$10B
                    fcf_score = 15
                elif fcf > 1e9:  # >$1B
                    fcf_score = 12
                elif fcf > 0:
                    fcf_score = 8
            else:
                fcf_score = 5  # 没有负面数据给部分分
            scores.append(fcf_score)
            details['cashflow'] = fcf_score
            
            # 5. 资产负债表 (10分)
            balance_score = 0
            debt_to_equity = info.get('debtToEquity')
            current_ratio = info.get('currentRatio')
            
            if debt_to_equity and current_ratio:
                if debt_to_equity < 50 and current_ratio > 1.5:
                    balance_score = 10
                elif debt_to_equity < 100 and current_ratio > 1.2:
                    balance_score = 7
                elif debt_to_equity < 150:
                    balance_score = 5
            else:
                balance_score = 5
            scores.append(balance_score)
            details['balance_sheet'] = balance_score
            
            total = sum(scores)
            return total, details
            
        except Exception as e:
            print(f"财务评分出错: {e}")
            return 50, {'error': str(e)}
    
    # ==================== 技术评分 ====================
    def _technical_score(self, symbol: str) -> Tuple[float, Dict]:
        """
        技术评分 (0-100)
        评估: 趋势、动量、相对强度、波动性
        """
        details = {}
        scores = []
        
        try:
            stock = yf.Ticker(symbol)
            
            # 获取历史数据
            hist = stock.history(period='6mo')
            if hist.empty:
                return 50, {'error': 'No data'}
            
            current_price = hist['Close'].iloc[-1]
            
            # 1. 趋势评分 (30分) - 价格 vs 均线
            trend_score = 0
            for period in [20, 50, 200]:
                if len(hist) >= period:
                    ma = hist['Close'].rolling(period).mean().iloc[-1]
                    if current_price > ma:
                        trend_score += 10
            details['trend'] = trend_score
            scores.append(trend_score)
            
            # 2. 动量评分 (30分) - RSI
            rsi = self._calculate_rsi(hist['Close'])
            momentum_score = 0
            if rsi < 30:
                momentum_score = 30  # 超卖，可能反弹
            elif rsi < 40:
                momentum_score = 25
            elif rsi < 50:
                momentum_score = 20
            elif rsi < 60:
                momentum_score = 15
            else:
                momentum_score = 10
            details['momentum'] = momentum_score
            details['rsi'] = round(rsi, 1)
            scores.append(momentum_score)
            
            # 3. 相对强度 (20分) - vs SPY
            try:
                spy = yf.Ticker('SPY')
                spy_hist = spy.history(period='3mo')
                if not spy_hist.empty:
                    stock_return = (current_price / hist['Close'].iloc[-60] - 1) * 100 if len(hist) >= 60 else 0
                    spy_return = (spy_hist['Close'].iloc[-1] / spy_hist['Close'].iloc[-60] - 1) * 100 if len(spy_hist) >= 60 else 0
                    
                    relative_score = 0
                    if stock_return > spy_return + 10:
                        relative_score = 20
                    elif stock_return > spy_return:
                        relative_score = 15
                    elif stock_return > -5:
                        relative_score = 10
                    else:
                        relative_score = 5
                    details['relative_strength'] = relative_score
                    scores.append(relative_score)
                else:
                    scores.append(10)
                    details['relative_strength'] = 10
            except:
                scores.append(10)
                details['relative_strength'] = 10
            
            # 4. 波动性评分 (20分) - ATR
            atr = self._calculate_atr(hist)
            volatility_score = 0
            atr_pct = (atr / current_price) * 100
            
            # 低波动率更好 (但不要太低)
            if 2 < atr_pct < 8:
                volatility_score = 20
            elif atr_pct < 12:
                volatility_score = 15
            elif atr_pct < 20:
                volatility_score = 10
            else:
                volatility_score = 5
            details['volatility'] = volatility_score
            details['atr_pct'] = round(atr_pct, 1)
            scores.append(volatility_score)
            
            total = sum(scores)
            return total, details
            
        except Exception as e:
            print(f"技术评分出错: {e}")
            return 50, {'error': str(e)}
    
    # ==================== 舆情评分 ====================
    def _sentiment_score(self, symbol: str) -> Tuple[float, Dict]:
        """
        舆情评分 (0-100)
        评估: 分析师评级、新闻情绪、法律风险、机构持仓
        """
        details = {}
        scores = []
        
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            # 1. 分析师评级 (30分) - 降低权重
            rating_score = 0
            recommendations = info.get('recommendationKey') or info.get('recommendationSummary')
            
            rating_map = {
                'buy': 30, 'strong-buy': 30, 'outperform': 28,
                'hold': 20, 'neutral': 20,
                'sell': 10, 'strong-sell': 5, 'underperform': 10
            }
            
            if recommendations:
                rating_score = rating_map.get(recommendations.lower(), 15)
            else:
                rating_score = 15
            details['analyst_rating'] = rating_score
            scores.append(rating_score)
            
            # 2. 法律/诉讼风险检测 (25分) - 新增
            legal_score = self._check_legal_risks(symbol)
            details['legal_risk'] = legal_score['score']
            details['legal_details'] = legal_score['details']
            scores.append(legal_score['score'])
            
            # 3. 新闻情绪 (20分) - 改为负面检测
            news_score = self._analyze_news_sentiment(symbol)
            details['news_sentiment'] = news_score['score']
            details['news_details'] = news_score['details']
            scores.append(news_score['score'])
            
            # 4. 机构持仓 (15分)
            institutional_score = 0
            held_by_inst = info.get('heldByInstitutions') or 0
            
            if held_by_inst > 80:
                institutional_score = 15
            elif held_by_inst > 60:
                institutional_score = 12
            elif held_by_inst > 40:
                institutional_score = 9
            else:
                institutional_score = 6
            details['institutional'] = institutional_score
            scores.append(institutional_score)
            
            # 5. 目标价vs当前价 (10分)
            target_score = 0
            target_mean = info.get('targetMeanPrice')
            current = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if target_mean and current:
                upside = (target_mean / current - 1) * 100
                if upside > 30:
                    target_score = 10
                elif upside > 15:
                    target_score = 8
                elif upside > 0:
                    target_score = 6
                elif upside > -15:
                    target_score = 4
                else:
                    target_score = 2  # 目标价低于现价
            else:
                target_score = 5
            
            details['target_price'] = target_score
            scores.append(target_score)
            
            total = sum(scores)
            return total, details
            
        except Exception as e:
            print(f"舆情评分出错: {e}")
            return 50, {'error': str(e)}
    
    def _check_legal_risks(self, symbol: str) -> Dict:
        """
        检测法律/诉讼风险
        高风险行业: 制药、医疗器械、能源、金融
        """
        # 高风险股票列表 (有重大诉讼历史)
        high_risk_stocks = {
            'JNJ': {'risk': 'high', 'issue': '滑石粉致癌诉讼'},
            'BA': {'risk': 'high', 'issue': '737 MAX事故诉讼'},
            'PG': {'risk': 'medium', 'issue': '爽身粉诉讼'},
            'MTCH': {'risk': 'medium', 'issue': '约会App监管'},
            'OXY': {'risk': 'medium', 'issue': '环境诉讼'},
            'GS': {'risk': 'medium', 'issue': 'ESG相关诉讼'},
        }
        
        # 高风险行业
        high_risk_sectors = ['healthcare', 'financial', 'energy', 'tobacco']
        
        if symbol in high_risk_stocks:
            risk_info = high_risk_stocks[symbol]
            if risk_info['risk'] == 'high':
                return {'score': 5, 'details': f"高风险: {risk_info['issue']}"}
            else:
                return {'score': 12, 'details': f"中风险: {risk_info['issue']}"}
        
        # 检查行业风险
        stock = yf.Ticker(symbol)
        sector = stock.info.get('sector', '').lower()
        
        if any(s in sector for s in ['health', 'pharma', 'medical']):
            return {'score': 15, 'details': '医疗行业默认风险'}
        
        return {'score': 25, 'details': '无重大法律风险'}
    
    def _analyze_news_sentiment(self, symbol: str) -> Dict:
        """
        分析新闻情绪 - 检测负面关键词
        """
        # 负面关键词
        negative_keywords = [
            'lawsuit', 'sued', 'settlement', 'recall', 'investigation',
            'fda', 'approval denied', 'scandal', 'fraud', 'bankruptcy',
            'layoff', 'cut jobs', 'violation', 'penalty', 'fine'
        ]
        
        try:
            stock = yf.Ticker(symbol)
            news = stock.news
            
            if not news or len(news) == 0:
                return {'score': 15, 'details': '无新闻数据'}
            
            # 简化检测 - 随机给分 (实际应该用NLP)
            # 这里用股票代码哈希模拟负面检测
            news_count = len(news)
            
            # 如果新闻多，给中等分数
            if news_count >= 5:
                return {'score': 15, 'details': f'新闻{news_count}条，中性'}
            else:
                return {'score': 12, 'details': f'新闻{news_count}条'}
                
        except:
            return {'score': 15, 'details': '无法获取新闻'}
    
    # ==================== 宏观政治评分 ====================
    def _macro_political_score(self, sector: str) -> Tuple[float, Dict]:
        """
        宏观政治评分 (0-100)
        评估: 利率环境、通胀、GDP增长、地缘政治
        """
        details = {}
        scores = []
        
        # 获取宏观数据
        macro_data = self._fetch_macro_data()
        
        # 获取行业敏感度
        sensitivity = self.industry_macro_sensitivity.get(sector, self.industry_macro_sensitivity['tech'])
        
        # 1. 利率环境评分 (25分)
        interest_score = self._score_interest_rate(macro_data, sensitivity.get('interest_rate', 0.25))
        details['interest_rate'] = interest_score
        scores.append(interest_score['score'])
        
        # 2. 通胀环境评分 (25分)
        inflation_score = self._score_inflation(macro_data, sensitivity.get('inflation', 0.25))
        details['inflation'] = inflation_score
        scores.append(inflation_score['score'])
        
        # 3. 经济增长评分 (25分)
        gdp_score = self._score_gdp(macro_data, sensitivity.get('gdp', 0.25))
        details['gdp'] = gdp_score
        scores.append(gdp_score['score'])
        
        # 4. 地缘政治评分 (25分)
        geo_score = self._score_geopolitics()
        details['geopolitics'] = geo_score
        scores.append(geo_score['score'])
        
        total = sum(scores)
        return total, details
    
    def _fetch_macro_data(self) -> Dict:
        """获取当前宏观数据"""
        data = {
            'fed_rate': 4.25,  # 默认值
            'inflation': 2.9,
            'gdp_growth': 2.3,
            'unemployment': 4.0,
            'dollar_index': 105.0,
            'treasury_10y': 4.3
        }
        
        try:
            # 尝试从Yahoo Finance获取美国10年国债收益率
            treasury = yf.Ticker('^TNX')
            hist = treasury.history(period='5d')
            if not hist.empty:
                data['treasury_10y'] = hist['Close'].iloc[-1]
        except:
            pass
        
        return data
    
    def _score_interest_rate(self, macro: Dict, weight: float) -> Dict:
        """利率评分"""
        rate = macro.get('treasury_10y', 4.0)
        
        # 对于大多数行业，高利率是负面
        if rate < 3.5:
            return {'score': 25, 'level': '低利率环境 - 利好', 'value': rate}
        elif rate < 4.5:
            return {'score': 18, 'level': '中性', 'value': rate}
        elif rate < 5.5:
            return {'score': 12, 'level': '高利率环境', 'value': rate}
        else:
            return {'score': 8, 'level': '极高利率', 'value': rate}
    
    def _score_inflation(self, macro: Dict, weight: float) -> Dict:
        """通胀评分"""
        inflation = macro.get('inflation', 3.0)
        
        if inflation < 2.0:
            return {'score': 25, 'level': '低通胀 - 理想', 'value': inflation}
        elif inflation < 3.0:
            return {'score': 20, 'level': '接近目标', 'value': inflation}
        elif inflation < 4.0:
            return {'score': 15, 'level': '中等通胀', 'value': inflation}
        elif inflation < 6.0:
            return {'score': 10, 'level': '高通胀', 'value': inflation}
        else:
            return {'score': 5, 'level': '恶性通胀', 'value': inflation}
    
    def _score_gdp(self, macro: Dict, weight: float) -> Dict:
        """GDP增长评分"""
        gdp = macro.get('gdp_growth', 2.0)
        
        if gdp > 3.0:
            return {'score': 25, 'level': '强劲增长', 'value': gdp}
        elif gdp > 2.0:
            return {'score': 20, 'level': '稳健增长', 'value': gdp}
        elif gdp > 1.0:
            return {'score': 15, 'level': '温和增长', 'value': gdp}
        elif gdp > 0:
            return {'score': 10, 'level': '低速增长', 'value': gdp}
        else:
            return {'score': 5, 'level': '经济衰退', 'value': gdp}
    
    def _score_geopolitics(self) -> Dict:
        """地缘政治评分 - 简化版"""
        # 简化: 基于当前主要风险事件
        # 实际生产应该接入新闻API实时分析
        
        score = 18  # 默认中性
        level = "中等风险"
        
        # 可以扩展更多事件检测
        return {'score': score, 'level': level, 'events': []}
    
    # ==================== 工具方法 ====================
    def _calculate_rsi(self, prices, period=14) -> float:
        """计算RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not rsi.iloc[-1:].isna().any() else 50
    
    def _calculate_atr(self, hist, period=14) -> float:
        """计算ATR"""
        high = hist['High']
        low = hist['Low']
        close = hist['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = tr1.combine(tr2, max).combine(tr3, max)
        atr = tr.rolling(period).mean()
        
        return atr.iloc[-1]
    
    # ==================== 建议生成 ====================
    def _generate_recommendation(self, score: float) -> Dict:
        """根据综合评分生成建议"""
        if score >= self.thresholds['strong_buy']:
            return {
                'action': 'STRONG_BUY',
                'emoji': '🚀',
                'rationale': '多维度数据显示强烈买入机会'
            }
        elif score >= self.thresholds['buy']:
            return {
                'action': 'BUY',
                'emoji': '🟢',
                'rationale': '基本面+技术面+情绪均支持上涨'
            }
        elif score >= self.thresholds['hold']:
            return {
                'action': 'HOLD',
                'emoji': '🟡',
                'rationale': '建议观望，等待更好时机'
            }
        elif score >= self.thresholds['sell']:
            return {
                'action': 'SELL',
                'emoji': '🔴',
                'rationale': '多个维度显示风险较高'
            }
        else:
            return {
                'action': 'STRONG_SELL',
                'emoji': '💥',
                'rationale': '建议回避，风险极大'
            }
    
    def format_report(self, result: Dict) -> List[str]:
        """格式化报告为消息列表"""
        messages = []
        
        # 标题
        rec = result['recommendation']
        msg = f"{rec['emoji']} *{result['symbol']} 综合评分报告*\n\n"
        msg += f"🎯 *综合评分: {result['overall_score']:.0f}/100* ({rec['action']})\n"
        msg += f"📊 评分时间: {result['timestamp'][:10]}\n\n"
        
        msg += "📈 *四维度评分*\n"
        scores = result['scores']
        msg += f"   财务: {scores['financial']:.0f}/100\n"
        msg += f"   技术: {scores['technical']:.0f}/100\n"
        msg += f"   舆情: {scores['sentiment']:.0f}/100\n"
        msg += f"   宏观: {scores['macro_political']:.0f}/100\n"
        
        messages.append(msg)
        
        # 详细分解
        details = result['details']
        
        # 财务详情
        fin = details.get('financial', {})
        msg = "📊 *财务详情*\n"
        if 'error' not in fin:
            msg += f"   盈利: {fin.get('profitability', 0)}/25\n"
            msg += f"   成长: {fin.get('growth', 0)}/25\n"
            msg += f"   估值: {fin.get('valuation', 0)}/25\n"
            msg += f"   现金流: {fin.get('cashflow', 0)}/15\n"
            msg += f"   资产: {fin.get('balance_sheet', 0)}/10\n"
        messages.append(msg)
        
        # 技术详情
        tech = details.get('technical', {})
        msg = "📈 *技术详情*\n"
        if 'error' not in tech:
            msg += f"   趋势: {tech.get('trend', 0)}/30\n"
            msg += f"   动量(RSI): {tech.get('momentum', 0)}/30 (RSI={tech.get('rsi', 'N/A')})\n"
            msg += f"   相对强度: {tech.get('relative_strength', 0)}/20\n"
            msg += f"   波动性: {tech.get('volatility', 0)}/20 (ATR={tech.get('atr_pct', 'N/A')}%)"
        messages.append(msg)
        
        # 舆情详情
        sent = details.get('sentiment', {})
        msg = "📰 *舆情详情*\n"
        if 'error' not in sent:
            msg += f"   分析师: {sent.get('analyst_rating', 0)}/40\n"
            msg += f"   关注度: {sent.get('news_score', 0)}/30\n"
            msg += f"   机构持仓: {sent.get('institutional', 0)}/20\n"
            msg += f"   目标价空间: {sent.get('target_price', 0)}/10\n"
        messages.append(msg)
        
        # 宏观详情
        macro = details.get('macro_political', {})
        msg = "🌍 *宏观政治*\n"
        if 'interest_rate' in macro:
            ir = macro['interest_rate']
            msg += f"   利率: {ir.get('value', 'N/A')}% → {ir.get('level', 'N/A')}\n"
        if 'inflation' in macro:
            inf = macro['inflation']
            msg += f"   通胀: {inf.get('value', 'N/A')}% → {inf.get('level', 'N/A')}\n"
        if 'gdp' in macro:
            gdp = macro['gdp']
            msg += f"   GDP: {gdp.get('value', 'N/A')}% → {gdp.get('level', 'N/A')}\n"
        if 'geopolitics' in macro:
            geo = macro['geopolitics']
            msg += f"   地缘: {geo.get('level', 'N/A')}\n"
        messages.append(msg)
        
        # 建议理由
        msg = f"💡 *建议*: {rec['rationale']}"
        messages.append(msg)
        
        return messages


# ==================== 行业宏观影响分析 ====================
class MacroImpactAnalyzer:
    """
    宏观经济与政治事件影响分析器
    """
    
    def __init__(self):
        # 主要宏观因子
        self.macro_factors = {
            'interest_rate': '利率',
            'inflation': '通胀',
            'gdp': 'GDP增长',
            'unemployment': '失业率',
            'dollar': '美元指数',
            'trade': '贸易政策',
            'regulation': '监管政策',
            'geopolitics': '地缘政治',
            'demographic': '人口结构'
        }
        
        # 政治事件影响映射
        self.political_events = {
            'fed_meeting': {'impact': 'high', 'sectors': ['finance', 'real_estate', 'utilities']},
            'election': {'impact': 'medium', 'sectors': ['healthcare', 'energy', 'tech']},
            'trade_war': {'impact': 'high', 'sectors': ['tech', 'industrial', 'consumer']},
            'war': {'impact': 'high', 'sectors': ['energy', 'defense', 'utilities']},
            'pandemic': {'impact': 'high', 'sectors': ['healthcare', 'tech', 'consumer']}
        }
    
    def analyze_industry_impact(self, sector: str, macro_changes: Dict) -> Dict:
        """
        分析宏观变化对特定行业的影响
        
        Args:
            sector: 行业 (tech, finance, energy, etc.)
            macro_changes: 宏观因子变化 {factor: change_direction}
                          change_direction: 1 (正面), 0 (中性), -1 (负面)
        
        Returns:
            影响分析结果
        """
        sensitivity = {
            'tech': {'interest_rate': -0.3, 'inflation': -0.2, 'gdp': 0.4, 'regulation': -0.3},
            'finance': {'interest_rate': 0.5, 'inflation': 0.2, 'gdp': 0.4, 'regulation': -0.3},
            'energy': {'inflation': 0.3, 'geopolitics': 0.5, 'dollar': -0.3},
            'healthcare': {'regulation': -0.4, 'gdp': 0.2, 'demographic': 0.3},
            'consumer': {'inflation': -0.3, 'gdp': 0.4, 'employment': 0.3},
            'industrial': {'gdp': 0.5, 'trade': -0.3, 'interest_rate': -0.2},
            'real_estate': {'interest_rate': -0.5, 'gdp': 0.3, 'regulation': -0.2},
            'utilities': {'interest_rate': -0.4, 'inflation': -0.3, 'regulation': -0.2}
        }
        
        sector_sensitivity = sensitivity.get(sector, {})
        total_impact = 0
        impacts = {}
        
        for factor, direction in macro_changes.items():
            weight = sector_sensitivity.get(factor, 0)
            impact = direction * weight
            total_impact += impact
            impacts[factor] = {
                'direction': direction,
                'weight': weight,
                'impact': impact
            }
        
        return {
            'sector': sector,
            'overall_impact': total_impact,
            'detailed_impacts': impacts,
            'recommendation': 'positive' if total_impact > 0.2 else 'negative' if total_impact < -0.2 else 'neutral'
        }
    
    def get_current_macro_outlook(self) -> Dict:
        """
        获取当前宏观环境概览
        简化版 - 实际应该接入实时数据
        """
        return {
            'interest_rate': {'level': 'high', 'trend': 'declining', 'value': 4.3},
            'inflation': {'level': 'moderate', 'trend': 'declining', 'value': 2.9},
            'gdp_growth': {'level': 'stable', 'trend': 'stable', 'value': 2.3},
            'unemployment': {'level': 'low', 'trend': 'stable', 'value': 4.0},
            'dollar': {'level': 'strong', 'trend': 'stable', 'value': 105}
        }


# 测试
if __name__ == "__main__":
    scoring = ComprehensiveScoringSystem()
    
    # 测试股票
    test_stocks = ['NVDA', 'AAPL', 'JPM', 'XOM', 'JNJ']
    
    for symbol in test_stocks:
        print(f"\n{'='*50}")
        print(f"分析 {symbol}...")
        
        # 根据代码判断行业
        tech_stocks = ['NVDA', 'AAPL', 'MSFT', 'GOOG', 'META']
        finance_stocks = ['JPM', 'BAC', 'GS', 'WFC']
        energy_stocks = ['XOM', 'CVX', 'COP']
        
        if symbol in tech_stocks:
            sector = 'tech'
        elif symbol in finance_stocks:
            sector = 'finance'
        elif symbol in energy_stocks:
            sector = 'energy'
        else:
            sector = 'healthcare'
        
        result = scoring.analyze(symbol, sector)
        
        messages = scoring.format_report(result)
        for m in messages:
            print(m)
            print("---")
