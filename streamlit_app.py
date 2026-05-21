import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Profi Swing-Trader Tool", page_icon="📈", layout="centered")
st.title("📈 Profi Swing-Trading Analysator")
st.markdown("Gib ein Aktien-Kürzel ein, um eine vollautomatische Profi-Analyse inklusive Live-Daten und Swing-Score zu erhalten.")

ticker_input = st.text_input("Aktien-Kürzel suchen (z.B. AAPL, TSLA, MSFT, SAP.DE):", value="AAPL").upper().strip()

if ticker_input:
    try:
        with st.spinner(f"Analysiere {ticker_input}..."):
            stock = yf.Ticker(ticker_input)
            hist = stock.history(period="3mo")
            info = stock.info
            
        if hist.empty:
            st.error("Keine Daten gefunden. Bitte überprüfe das Aktien-Kürzel.")
    except Exception as e:
        st.error(f"Fehler beim Laden: {e}")
        hist = pd.DataFrame()

    if not hist.empty:
        current_price = round(hist['Close'].iloc[-1], 2)
        currency = info.get('currency', '$')
        long_name = info.get('longName', ticker_input)
        
        st.subheader(f"Ergebnis für: {long_name} ({ticker_input})")
        st.metric(label="Aktueller Live-Kurs", value=f"{current_price} {currency}")

        # Berechnungen
        hist['EMA20'] = hist['Close'].ewm(span=20, adjust=False).mean()
        hist['SMA50'] = hist['Close'].rolling(window=50).mean()
        last_close = hist['Close'].iloc[-1]
        last_ema20 = hist['EMA20'].iloc[-1]
        last_sma50 = hist['SMA50'].iloc[-1]

        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        hist['RSI'] = 100 - (100 / (1 + rs))
        current_rsi = round(hist['RSI'].iloc[-1], 2) if not pd.isna(hist['RSI'].iloc[-1]) else 50

        exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
        exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
        hist['MACD'] = exp1 - exp2
        hist['Signal'] = hist['MACD'].ewm(span=9, adjust=False).mean()
        last_macd = hist['MACD'].iloc[-1]
        last_sig = hist['Signal'].iloc[-1]

        avg_volume = hist['Volume'].mean()
        last_volume = hist['Volume'].iloc[-1]

        st.markdown("---")
        st.subheader("📰 News-Katalysator (Manuelle Einschätzung)")
        news_sentiment = st.selectbox(
            "Wie ist die fundamentale Newslage der Aktie?",
            ["Sehr Positiv (Zahlen geschlagen, Upgrade, Hype)", "Neutral (Keine großen News)", "Negativ (Ausblick gesenkt, Downgrade)"]
        )

        # Score-Logik
        score = 0
        details = []

        if 40 <= current_rsi <= 55:
            score += 20
            details.append(f"🟢 **RSI ({current_rsi}):** Perfekter Rücksetzer im Aufwärtstrend (+20 Pkt.)")
        elif 30 <= current_rsi < 40:
            score += 15
            details.append(f"🟡 **RSI ({current_rsi}):** Leicht überverkauft (+15 Pkt.)")
        elif 55 < current_rsi <= 68:
            score += 12
            details.append(f"🔵 **RSI ({current_rsi}):** Aufwärts-Momentum (+12 Pkt.)")
        else:
            details.append(f"🔴 **RSI ({current_rsi}):** Überkauft oder freier Fall (+0 Pkt.)")

        if last_close > last_ema20 and last_close > last_sma50:
            score += 20
            details.append("🟢 **Trend:** Aktie über EMA 20 & SMA 50. Starker Aufwärtstrend! (+20 Pkt.)")
        elif last_close > last_ema20:
            score += 10
            details.append("🟡 **Trend:** Über EMA 20, kurzfristige Erholung (+10 Pkt.)")
        else:
            details.append("🔴 **Trend:** Im Abwärtstrend (+0 Pkt.)")

        if last_macd > last_sig:
            score += 20
            details.append("🟢 **MACD:** Bullish Crossover! (+20 Pkt.)")
        else:
            details.append("🔴 **MACD:** Bearish. Verkaufsdruck überwiegt (+0 Pkt.)")

        if last_volume > avg_volume:
            score += 15
            details.append("🟢 **Volumen:** Überdurchschnittlich. Institutionelle Käufer aktiv (+15 Pkt.)")
        else:
            score += 7
            details.append("🟡 **Volumen:** Durchschnittliches Interesse (+7 Pkt.)")

        if "Sehr Positiv" in news_sentiment:
            score += 25
            details.append("🟢 **News:** Starker fundamentaler Rückenwind (+25 Pkt.)")
        elif "Neutral" in news_sentiment:
            score += 10
            details.append("🟡 **News:** Keine klaren Impulse (+10 Pkt.)")
        else:
            details.append("🔴 **News:** Schlechte Nachrichten belasten (+0 Pkt.)")

        st.markdown("---")
        st.subheader("📊 Das Profi-Testergebnis")
        
        if score >= 75:
            st.success(f"🔥 **SWING-SCORE: {score} / 100** -> **STARKER KAUF**")
        elif 60 <= score < 75:
            st.info(f"⚡ **SWING-SCORE: {score} / 100** -> **POTENZIELLER KAUF**")
        elif 40 <= score < 60:
            st.warning(f"⏳ **SWING-SCORE: {score} / 100** -> **HALTEN / BEOBACHTEN**")
        else:
            st.error(f"❌ **SWING-SCORE: {score} / 100** -> **MEIDEN / SHORT**")

        with st.expander("Punkte-Aufschlüsselung ansehen"):
            for line in details:
                st.write(line)

        st.markdown("---")
        st.subheader("🛡️ Risikomanagement (CRV 1:3)")
        stop_loss = round(current_price * 0.96, 2)
        take_profit = round(current_price * 1.12, 2)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Einstieg", f"{current_price} {currency}")
        col2.metric("🛑 STOP-LOSS", f"{stop_loss} {currency}", "-4%")
        col3.metric("🎯 TAKE-PROFIT", f"{take_profit} {currency}", "+12%")
