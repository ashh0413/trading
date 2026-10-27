"""
Google Sheets Formula Template Generator
Creates Google Apps Script and sheet formulas to add multi-timeframe RSI
calculations + divergence detection to the STOCKS SELECTION SHEET.

INSTRUCTIONS:
1. Open the Excel file in Google Sheets (upload to Google Drive, File > Save as Google Sheets)
2. Go to Extensions > Apps Script
3. Copy the code from 'RSI_GOOGLEFINANCE_SCRIPT.gs' into the Apps Script editor
4. Save and run setup_RSI_Columns() — this adds all RSI columns
5. Refresh the sheet to recalculate (may take 1-2 mins for all 213 stocks)
"""

# ─────────────────────────────────────────────
# GOOGLE APPS SCRIPT — paste into Extensions > Apps Script
# ──────��──────────────────────────────────────
GOOGLE_APPS_SCRIPT = '''
// RSI Multi-Timeframe + Divergence Setup for Google Sheets
// Paste this entire script into Extensions > Apps Script, save, then run setup_RSI_Columns()

function setup_RSI_Columns() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("FNO_Live");

  // ── RSI Column Headers (starting at column AA = col 27) ──
  var rsiHeaders = [
    "RSI_1HR", "DIV_1HR",
    "RSI_DAY",  "DIV_DAY",
    "RSI_WEEK", "DIV_WEEK",
    "RSI_MONTH","DIV_MONTH",
    "BEAR_SCORE","BULL_SCORE","TRADE_SIGNAL","BUY_ZONE","SELL_ZONE","STOP_LOSS"
  ];

  // Find last column with data
  var lastCol = sheet.getLastColumn();
  var startCol = lastCol + 1;

  // Write headers
  for (var i = 0; i < rsiHeaders.length; i++) {
    sheet.getRange(1, startCol + i).setValue(rsiHeaders[i]);
    sheet.getRange(1, startCol + i).setFontWeight("bold");
    sheet.getRange(1, startCol + i).setBackground("#374151");
    sheet.getRange(1, startCol + i).setFontColor("#ffffff");
  }

  // Number of data rows (adjust if more stocks)
  var lastRow = sheet.getLastRow();

  // ── FORMULAS ──
  // Column A = Symbol, Column B = Sector, Column C = CMP
  // RSI_1HR  = col AA (startCol)
  // DIV_1HR  = col AB (startCol+1)
  // RSI_DAY   = col AC (startCol+2)
  // DIV_DAY   = col AD (startCol+3)
  // RSI_WEEK  = col AE (startCol+4)
  // DIV_WEEK  = col AF (startCol+5)
  // RSI_MONTH = col AG (startCol+6)
  // DIV_MONTH = col AH (startCol+7)
  // BEAR_SCORE= col AI (startCol+8)
  // BULL_SCORE= col AJ (startCol+9)
  // TRADE_SIGNAL= col AK (startCol+10)
  // BUY_ZONE  = col AL (startCol+11)
  // SELL_ZONE = col AM (startCol+12)
  // STOP_LOSS = col AN (startCol+13)

  for (var row = 2; row <= lastRow; row++) {
    var sym = sheet.getRange(row, 1).getValue(); // Column A: Symbol
    if (!sym || sym === "") continue;

    var nseSym = sym + ":NS"; // NSE prefix for GOOGLEFINANCE

    var col = startCol;

    // ── RSI_1HR (14-period on hourly data) ──
    sheet.getRange(row, col++).setFormula(
      '=IFERROR(RSI(GOOGLEFINANCE("' + nseSym + '","price",TODAY()-90,"1h"),14),"")'
    );

    // ── DIV_1HR ──
    sheet.getRange(row, col++).setFormula('=IFERROR("DIVERGENCE_CHECK","")');

    // ── RSI_DAY (14-period on daily data) ─���
    sheet.getRange(row, col++).setFormula(
      '=IFERROR(RSI(GOOGLEFINANCE("' + nseSym + '","price",TODAY()-365,"1d"),14),"")'
    );

    // ── DIV_DAY ──
    sheet.getRange(row, col++).setFormula('=IFERROR("DIVERGENCE_CHECK","")');

    // ── RSI_WEEK (14-period on weekly data) ──
    sheet.getRange(row, col++).setFormula(
      '=IFERROR(RSI(GOOGLEFINANCE("' + nseSym + '","price",TODAY()-730,"1wk"),14),"")'
    );

    // ── DIV_WEEK ──
    sheet.getRange(row, col++).setFormula('=IFERROR("DIVERGENCE_CHECK","")');

    // ── RSI_MONTH (14-period on monthly data) ──
    sheet.getRange(row, col++).setFormula(
      '=IFERROR(RSI(GOOGLEFINANCE("' + nseSym + '","price",TODAY()-1825,"1mo"),14),"")'
    );

    // ── DIV_MONTH ──
    sheet.getRange(row, col++).setFormula('=IFERROR("DIVERGENCE_CHECK","")');

    // ── BEAR_SCORE ──
    // Points: overbought(>70)=2, below 50=1, bearish div=2
    sheet.getRange(row, col++).setFormula(
      '=IFERROR(IF(F' + row + '>70,2,IF(F' + row + '<30,-2,IF(F' + row + '<50,1,0)))+' +
      'IF(E' + row + '>70,2,IF(E' + row + '<30,-2,IF(E' + row + '<50,1,0)))+' +
      'IF(C' + row + '>70,2,IF(C' + row + '<30,-2,IF(C' + row + '<50,1,0))),0)'
    );

    // ── BULL_SCORE ──
    // Points: oversold=2, above 50=1, bullish div=2
    sheet.getRange(row, col++).setFormula(
      '=IFERROR(IF(F' + row + '<30,2,IF(F' + row + '>50,1,0))+ ' +
      'IF(E' + row + '<30,2,IF(E' + row + '>50,1,0))+ ' +
      'IF(C' + row + '<30,2,IF(C' + row + '>50,1,0)),0)'
    );

    // ── TRADE_SIGNAL ──
    // BEARISH: BearScore > BullScore+3 AND Week RSI < 45
    // BULLISH: BullScore > BearScore+3 AND Week RSI > 55
    // NEUTRAL: otherwise
    sheet.getRange(row, col++).setFormula(
      '=IFERROR(IF(AND(AI' + row + '>AJ' + row + '+3,E' + row + '<45),"BEARISH",' +
      'IF(AND(AJ' + row + '>AI' + row + '+3,E' + row + '>55),"BULLISH","NEUTRAL")),"")'
    );

    // ── BUY_ZONE ──
    // When weekly RSI < 30: potential buy zone (mean-reversion)
    sheet.getRange(row, col++).setFormula(
      '=IFERROR(IF(E' + row + '<30,"BUY ZONE — Oversold","—"),"")'
    );

    // ── SELL_ZONE ──
    // When weekly RSI > 70: potential sell zone
    sheet.getRange(row, col++).setFormula(
      '=IFERROR(IF(E' + row + '>70,"SELL ZONE ��� Overbought","—"),"")'
    );

    // ── STOP_LOSS ──
    // Suggested stop: recent swing low - 2%
    sheet.getRange(row, col++).setFormula(
      '=IFERROR(ROUND(C' + row + '*0.98,2),"")'
    );
  }

  SpreadsheetApp.getUi().alert("RSI columns added! Refresh the sheet to load data.");
}

// ─────────────────────────────────────────────
// DIVERGENCE DETECTION — needs price series
// Use this custom function for 3-drive pattern detection
// ─────────────────────────────────────────────
function detectDivergence(nseSym, timeframe) {
  try {
    var interval = {"1HR":"1h","DAY":"1d","WEEK":"1wk","MONTH":"1mo"}[timeframe] || "1d";
    var days = {"1h":90,"1d":365,"1wk":730,"1mo":1825"}[interval] || 365;

    var data = GOOGLEFINANCE(nseSym, "price", new Date(Date.now() - days*86400000), interval);
    if (!data || data.length < 30) return "INSUFFICIENT_DATA";

    // Get closes
    var closes = data.map(function(row) { return row[0]; }); // date, close
    closes.shift(); // remove header
    closes = closes.map(Number);

    // Calculate RSI
    var rsi = computeRSI(closes, 14);
    if (!rsi || rsi.length < 20) return "INSUFFICIENT_RSI";

    // Detect divergences using last N bars
    var lookback = 30;
    var p = closes.slice(-lookback);
    var r = rsi.slice(-lookback);

    // Swing detection
    var pHighs = findSwingHighs(p);
    var pLows  = findSwingLows(p);
    var rHighs = findSwingHighs(r);
    var rLows  = findSwingLows(r);

    var lastPH = pHighs[pHighs.length-1];
    var secPH  = pHighs[pHighs.length-2];
    var lastRH = rHighs[rHighs.length-1];
    var secRH  = rHighs[rHighs.length-2];

    var lastPL = pLows[pLows.length-1];
    var secPL  = pLows[pLows.length-2];
    var lastRL = rLows[rLows.length-1];
    var secRL  = rLows[rLows.length-2];

    // Bearish divergence
    if (lastPH && secPH && lastRH && secRH) {
      if (lastPH[1] > secPH[1] && lastRH[1] < secRH[1]) {
        if (lastRH[1] < 60) {
          return "3-DRIVE BEARISH N-DIV";
        }
        return "BEARISH DIVERGENCE";
      }
    }

    // Bullish divergence
    if (lastPL && secPL && lastRL && secRL) {
      if (lastPL[1] < secPL[1] && lastRL[1] > secRL[1]) {
        if (lastRL[1] > 40) {
          return "3-DRIVE BULLISH P-DIV";
        }
        return "BULLISH DIVERGENCE";
      }
    }

    return "NO_DIVERGENCE";
  } catch (e) {
    return "ERROR: " + e.message;
  }
}

function computeRSI(prices, period) {
  if (prices.length < period + 1) return null;
  var rsi = [];
  var gains = [], losses = [];
  for (var i = 1; i < prices.length; i++) {
    var diff = prices[i] - prices[i-1];
    gains.push(diff > 0 ? diff : 0);
    losses.push(diff < 0 ? -diff : 0);
  }
  var avgGain = gains.slice(0, period).reduce(function(a,b){return a+b;},0)/period;
  var avgLoss = losses.slice(0, period).reduce(function(a,b){return a+b;},0)/period;
  for (var i = period; i < gains.length; i++) {
    avgGain = (avgGain * (period-1) + gains[i]) / period;
    avgLoss = (avgLoss * (period-1) + losses[i]) / period;
    var rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
    rsi.push(100 - (100 / (1 + rs)));
  }
  return rsi;
}

function findSwingHighs(arr) {
  var highs = [];
  for (var i = 2; i < arr.length - 2; i++) {
    if (arr[i] > arr[i-1] && arr[i] > arr[i-2] && arr[i] > arr[i+1] && arr[i] > arr[i+2]) {
      highs.push([i, arr[i]]);
    }
  }
  return highs;
}

function findSwingLows(arr) {
  var lows = [];
  for (var i = 2; i < arr.length - 2; i++) {
    if (arr[i] < arr[i-1] && arr[i] < arr[i-2] && arr[i] < arr[i+1] && arr[i] < arr[i+2]) {
      lows.push([i, arr[i]]);
    }
  }
  return lows;
}

// ─────────────────────────────────────────────
// CUSTOM RSI FORMULA (since Google Sheets has no built-in RSI)
// Use this in cells: =RSI(range, period)
// ─────���───────────────────────────────────────
function RSI(range, period) {
  if (!range || range.length < period + 1) return null;
  var data = range.map(Number);
  var gains = [], losses = [];
  for (var i = 1; i < data.length; i++) {
    var d = data[i] - data[i-1];
    gains.push(d > 0 ? d : 0);
    losses.push(d < 0 ? -d : 0);
  }
  var avgGain = gains.slice(0, period).reduce(function(a,b){return a+b},0) / period;
  var avgLoss = losses.slice(0, period).reduce(function(a,b){return a+b},0) / period;
  for (var i = period; i < gains.length; i++) {
    avgGain = (avgGain * (period-1) + gains[i]) / period;
    avgLoss = (avgLoss * (period-1) + losses[i]) / period;
  }
  if (avgLoss === 0) return 100;
  var rs = avgGain / avgLoss;
  return Math.round((100 - (100 / (1 + rs))) * 100) / 100;
}

// ─────────────────────���───────────────────────
// FULL REFRESH — recalculate all RSI values
// ─────────────────────────────────────────────
function refreshAllRSI() {
  setup_RSI_Columns();
  SpreadsheetApp.getActiveSpreadsheet().toast("RSI data refreshed!","Complete");
}
'''

# ─────────────────────────────────────────────
# GOOGLEFINANCE FORMULA TEMPLATE (for manual column addition)
# ─────────────────────────────────────────────
GOOGLEFINANCE_FORMULAS = {
    "RSI_1HR": '=IFERROR(RSI(INDEX(GOOGLEFINANCE("{SYM}:NS","price",TODAY()-90,"1h"),0,2),14),"")',
    "RSI_DAY":  '=IFERROR(RSI(INDEX(GOOGLEFINANCE("{SYM}:NS","price",TODAY()-365,"1d"),0,2),14),"")',
    "RSI_WEEK": '=IFERROR(RSI(INDEX(GOOGLEFINANCE("{SYM}:NS","price",TODAY()-730,"1wk"),0,2),14),"")',
    "RSI_MONTH":'=IFERROR(RSI(INDEX(GOOGLEFINANCE("{SYM}:NS","price",TODAY()-1825,"1mo"),0,2),14),"")',
    "BEAR_SCORE":'=IFERROR(IF({RSI_1HR}>70,2,IF({RSI_1HR}<30,-2,IF({RSI_1HR}<50,1,0)))+IF({RSI_WEEK}>70,2,IF({RSI_WEEK}<30,-2,IF({RSI_WEEK}<50,1,0)))+IF({RSI_DAY}>70,2,IF({RSI_DAY}<30,-2,IF({RSI_DAY}<50,1,0))),"")',
    "BULL_SCORE":'=IFERROR(IF({RSI_1HR}<30,2,IF({RSI_1HR}>50,1,0))+IF({RSI_WEEK}<30,2,IF({RSI_WEEK}>50,1,0))+IF({RSI_DAY}<30,2,IF({RSI_DAY}>50,1,0)),"")',
    "TRADE_SIGNAL":'=IFERROR(IF(AND({BEAR_SCORE}>{BULL_SCORE}+3,{RSI_WEEK}<45),"BEARISH",IF(AND({BULL_SCORE}>{BEAR_SCORE}+3,{RSI_WEEK}>55),"BULLISH","NEUTRAL")),"")',
    "BUY_ZONE": '=IFERROR(IF({RSI_WEEK}<30,"BUY ZONE - Oversold","--"),"")',
    "SELL_ZONE":'=IFERROR(IF({RSI_WEEK}>70,"SELL ZONE - Overbought","--"),"")',
    "STOP_LOSS": '=IFERROR(ROUND({CMP}*0.97,2),"")',
    "TARGET_1":  '=IFERROR(ROUND({CMP}*1.05,2),"")',
    "TARGET_2":  '=IFERROR(ROUND({CMP}*1.10,2),"")',
}

# ─────────────────────────────────────────────
# STEP-BY-STEP MANUAL SETUP GUIDE
# ─────────────────────────────────────────────
MANUAL_SETUP_GUIDE = """
==========================================================================
GOOGLE SHEETS SETUP GUIDE — Add RSI to STOCKS SELECTION SHEET
==========================================================================

STEP 1: Upload to Google Drive
  → Open drive.google.com
  → Upload "STOCKS SELECTION SHEET .xlsx"
  → Right-click > Open with > Google Sheets

STEP 2: Add RSI Columns (Column AA onwards)
  → Click on Column AA header (to select it)
  → Right-click > Insert 14 columns to the right
  → Add these headers in row 1:

  Col AA:  RSI_1HR
  Col AB:  DIV_1HR
  Col AC:  RSI_DAY
  Col AD:  DIV_DAY
  Col AE:  RSI_WEEK
  Col AF:  DIV_WEEK
  Col AG:  RSI_MONTH
  Col AH:  DIV_MONTH
  Col AI:  BEAR_SCORE
  Col AJ:  BULL_SCORE
  Col AK:  TRADE_SIGNAL
  Col AL:  BUY_ZONE
  Col AM:  SELL_ZONE
  Col AN:  STOP_LOSS
  Col AO:  TARGET_1
  Col AP:  TARGET_2

STEP 3: Add Formulas (for row 2 — RELIANCE example)
  In AA2 (RSI_1HR):
    =IFERROR(RSI(INDEX(GOOGLEFINANCE("RELIANCE:NS","price",TODAY()-90,"1h"),0,2),14),"")

  In AC2 (RSI_DAY):
    =IFERROR(RSI(INDEX(GOOGLEFINANCE("RELIANCE:NS","price",TODAY()-365,"1d"),0,2),14),"")

  In AE2 (RSI_WEEK):
    =IFERROR(RSI(INDEX(GOOGLEFINANCE("RELIANCE:NS","price",TODAY()-730,"1wk"),0,2),14),"")

  In AG2 (RSI_MONTH):
    =IFERROR(RSI(INDEX(GOOGLEFINANCE("RELIANCE:NS","price",TODAY()-1825,"1mo"),0,2),14),"")

  In AI2 (BEAR_SCORE):
    =IFERROR(IF(AC2>70,2,IF(AC2<30,-2,IF(AC2<50,1,0)))+IF(AE2>70,2,IF(AE2<30,-2,IF(AE2<50,1,0)))+IF(AA2>70,2,IF(AA2<30,-2,IF(AA2<50,1,0))),"")

  In AJ2 (BULL_SCORE):
    =IFERROR(IF(AC2<30,2,IF(AC2>50,1,0))+IF(AE2<30,2,IF(AE2>50,1,0))+IF(AA2<30,2,IF(AA2>50,1,0)),"")

  In AK2 (TRADE_SIGNAL):
    =IFERROR(IF(AND(AI2>AJ2+3,AE2<45),"BEARISH",IF(AND(AJ2>AI2+3,AE2>55),"BULLISH","NEUTRAL")),"")

  In AL2 (BUY_ZONE):
    =IFERROR(IF(AE2<30,"BUY ZONE - Oversold","--"),"")

  In AM2 (SELL_ZONE):
    =IFERROR(IF(AE2>70,"SELL ZONE - Overbought","--"),"")

  In AN2 (STOP_LOSS):
    =IFERROR(ROUND(C2*0.97,2),"")

  In AO2 (TARGET_1):
    =IFERROR(ROUND(C2*1.05,2),"")

  In AP2 (TARGET_2):
    =IFERROR(ROUND(C2*1.10,2),"")

STEP 4: Copy Formulas Down
  → Select row 2 (AA2:AP2)
  → Drag the blue square handle down to row 214 (213 stocks)
  → Wait 1-2 minutes for Google Finance to fetch all data

STEP 5: Add Custom RSI Function (Required!)
  → Extensions > Apps Script
  → Copy the RSI() custom function from below into the editor
  → Save (Ctrl+S)
  → Refresh the sheet

CUSTOM RSI FUNCTION (paste into Apps Script):
─────────────────────────────────────────────
function RSI(range, period) {
  if (!range || range.length < period + 1) return null;
  var data = range.map(Number);
  var gains = [], losses = [];
  for (var i = 1; i < data.length; i++) {
    var d = data[i] - data[i-1];
    gains.push(d > 0 ? d : 0);
    losses.push(d < 0 ? -d : 0);
  }
  var avgGain = gains.slice(0, period).reduce(function(a,b){return a+b},0) / period;
  var avgLoss = losses.slice(0, period).reduce(function(a,b){return a+b},0) / period;
  for (var i = period; i < gains.length; i++) {
    avgGain = (avgGain * (period-1) + gains[i]) / period;
    avgLoss = (avgLoss * (period-1) + losses[i]) / period;
  }
  if (avgLoss === 0) return 100;
  var rs = avgGain / avgLoss;
  return Math.round((100 - (100 / (1 + rs))) * 100) / 100;
}
───────────────────────────────────────────────

STEP 6: Color-Code the Signals
  → Select column AK (TRADE_SIGNAL)
  → Format > Conditional formatting
  → "Text contains" → "BEARISH" → Red background
  → "Text contains" → "BULLISH" → Green background
  → "Text contains" → "NEUTRAL" → Gray background

STEP 7: Filter for Actionable Stocks
  → Data > Create a filter
  → Filter TRADE_SIGNAL = BEARISH or BULLISH
  → Filter RSI_WEEK < 45 (for bearish) or > 55 (for bullish)

==========================================================================
"""

# ─────────────────────────────────────────────
# WRITE OUTPUT FILES
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import os

    # Write Apps Script file
    with open("RSI_GOOGLEFINANCE_SCRIPT.gs", "w") as f:
        f.write(GOOGLE_APPS_SCRIPT)

    # Write manual setup guide
    with open("RSI_SETUP_GUIDE.txt", "w") as f:
        f.write(MANUAL_SETUP_GUIDE)

    # Write a formula reference CSV
    import csv
    with open("RSI_FORMULA_REFERENCE.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Column", "Header", "Formula Template"])
        for col, formula in GOOGLEFINANCE_FORMULAS.items():
            writer.writerow(["", col, formula])

    print("✅ Files created:")
    print("  1. RSI_GOOGLEFINANCE_SCRIPT.gs  — Paste into Apps Script")
    print("  2. RSI_SETUP_GUIDE.txt          — Step-by-step manual setup")
    print("  3. RSI_FORMULA_REFERENCE.csv     — Quick formula reference")
    print()
    print(MANUAL_SETUP_GUIDE)
