// RSI Multi-Timeframe + Divergence Setup for Google Sheets
// Paste into Extensions > Apps Script, save, then run setup_RSI_Columns()

function setup_RSI_Columns() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("FNO_Live");
  if (!sheet) {
    SpreadsheetApp.getUi().alert("Sheet 'FNO_Live' not found!");
    return;
  }
  var lastRow = sheet.getLastRow();
  var lastCol = sheet.getLastColumn();
  var startCol = lastCol + 1;

  var headers = [
    "RSI_1HR","DIV_1HR",
    "RSI_DAY","DIV_DAY",
    "RSI_WEEK","DIV_WEEK",
    "RSI_MONTH","DIV_MONTH",
    "BEAR_SCORE","BULL_SCORE",
    "TRADE_SIGNAL","BUY_ZONE","SELL_ZONE","STOP_LOSS"
  ];

  for (var i = 0; i < headers.length; i++) {
    var cell = sheet.getRange(1, startCol + i);
    cell.setValue(headers[i]);
    cell.setFontWeight("bold");
    cell.setBackground("#1f2937");
    cell.setFontColor("#ffffff");
  }

  function colLetter(n) {
    var letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    if (n <= 26) return letters[n - 1];
    return letters[Math.floor((n - 1) / 26) - 1] + letters[(n - 1) % 26];
  }

  var c1hr  = colLetter(startCol);
  var cDay  = colLetter(startCol + 2);
  var cWeek = colLetter(startCol + 4);
  var cBear = colLetter(startCol + 8);
  var cBull = colLetter(startCol + 9);

  for (var row = 2; row <= lastRow; row++) {
    var sym = sheet.getRange(row, 1).getValue();
    if (!sym || sym === "") continue;
    var nse = sym + ":NS";
    var col = startCol;

    // RSI_1HR
    sheet.getRange(row, col++).setFormula(
      '=IFERROR(RSI(INDEX(GOOGLEFINANCE("' + nse + '","price",TODAY()-90,"1h"),0,2),14),"")'
    );
    // DIV_1HR
    sheet.getRange(row, col++).setFormula('=IFERROR(detectDivergence("' + nse + '","1HR"),"")');
    // RSI_DAY
    sheet.getRange(row, col++).setFormula(
      '=IFERROR(RSI(INDEX(GOOGLEFINANCE("' + nse + '","price",TODAY()-365,"1d"),0,2),14),"")'
    );
    // DIV_DAY
    sheet.getRange(row, col++).setFormula('=IFERROR(detectDivergence("' + nse + '","DAY"),"")');
    // RSI_WEEK
    sheet.getRange(row, col++).setFormula(
      '=IFERROR(RSI(INDEX(GOOGLEFINANCE("' + nse + '","price",TODAY()-730,"1wk"),0,2),14),"")'
    );
    // DIV_WEEK
    sheet.getRange(row, col++).setFormula('=IFERROR(detectDivergence("' + nse + '","WEEK"),"")');
    // RSI_MONTH
    sheet.getRange(row, col++).setFormula(
      '=IFERROR(RSI(INDEX(GOOGLEFINANCE("' + nse + '","price",TODAY()-1825,"1mo"),0,2),14),"")'
    );
    // DIV_MONTH
    sheet.getRange(row, col++).setFormula('=IFERROR(detectDivergence("' + nse + '","MONTH"),"")');

    // BEAR_SCORE
    sheet.getRange(row, col++).setFormula(
      '=IFERROR(' +
      'IF(' + c1hr + row + '>70,2,IF(' + c1hr + row + '<30,-2,IF(' + c1hr + row + '<50,1,0)))+' +
      'IF(' + cWeek + row + '>70,2,IF(' + cWeek + row + '<30,-2,IF(' + cWeek + row + '<50,1,0)))+' +
      'IF(' + cDay + row + '>70,2,IF(' + cDay + row + '<30,-2,IF(' + cDay + row + '<50,1,0))),0)'
    );
    // BULL_SCORE
    sheet.getRange(row, col++).setFormula(
      '=IFERROR(' +
      'IF(' + c1hr + row + '<30,2,IF(' + c1hr + row + '>50,1,0))+ ' +
      'IF(' + cWeek + row + '<30,2,IF(' + cWeek + row + '>50,1,0))+ ' +
      'IF(' + cDay + row + '<30,2,IF(' + cDay + row + '>50,1,0)),0)'
    );
    // TRADE_SIGNAL
    sheet.getRange(row, col++).setFormula(
      '=IFERROR(IF(AND(' + cBear + row + '>' + cBull + row + '+3,' + cWeek + row + '<45),"BEARISH",' +
      'IF(AND(' + cBull + row + '>' + cBear + row + '+3,' + cWeek + row + '>55),"BULLISH","NEUTRAL")),"")'
    );
    // BUY_ZONE
    sheet.getRange(row, col++).setFormula(
      '=IFERROR(IF(' + cWeek + row + '<30,"BUY ZONE - Oversold","--"),"")'
    );
    // SELL_ZONE
    sheet.getRange(row, col++).setFormula(
      '=IFERROR(IF(' + cWeek + row + '>70,"SELL ZONE - Overbought","--"),"")'
    );
    // STOP_LOSS
    sheet.getRange(row, col++).setFormula('=IFERROR(ROUND(C' + row + '*0.98,2),"")');
  }

  sheet.setFrozenRows(1);
  SpreadsheetApp.getUi().alert("RSI columns added! Refresh the sheet (wait 1-2 mins).");
}

// Custom RSI — paste into Apps Script (Google Sheets has no built-in RSI)
function RSI(range, period) {
  if (!range || range.length < period + 1) return null;
  var data = range.map(Number);
  var gains = [], losses = [];
  for (var i = 1; i < data.length; i++) {
    var d = data[i] - data[i - 1];
    gains.push(d > 0 ? d : 0);
    losses.push(d < 0 ? -d : 0);
  }
  var avgGain = gains.slice(0, period).reduce(function(a, b) { return a + b; }, 0) / period;
  var avgLoss = losses.slice(0, period).reduce(function(a, b) { return a + b; }, 0) / period;
  for (var i = period; i < gains.length; i++) {
    avgGain = (avgGain * (period - 1) + gains[i]) / period;
    avgLoss = (avgLoss * (period - 1) + losses[i]) / period;
  }
  if (avgLoss === 0) return 100;
  var rs = avgGain / avgLoss;
  return Math.round((100 - (100 / (1 + rs))) * 100) / 100;
}

// Detect divergences — paste into Apps Script
// Usage: =detectDivergence("RELIANCE:NS", "WEEK")
function detectDivergence(nseSym, tf) {
  try {
    var im = { "1HR": "1h", "DAY": "1d", "WEEK": "1wk", "MONTH": "1mo" };
    var dm = { "1h": 90, "1d": 365, "1wk": 730, "1mo": 1825 };
    var interval = im[tf] || "1d";
    var days = dm[interval] || 365;
    var endDate = new Date();
    var startDate = new Date(endDate.getTime() - days * 86400000);
    var data = GOOGLEFINANCE(nseSym, "price", startDate, interval);
    if (!data || data.length < 30) return "INSUFFICIENT_DATA";
    var closes = [];
    for (var i = 1; i < data.length; i++) closes.push(Number(data[i][0]));
    var rsi = computeRSI(closes, 14);
    if (!rsi || rsi.length < 20) return "INSUFFICIENT_RSI";
    var lookback = Math.min(30, closes.length - 1);
    var p = closes.slice(-lookback);
    var r = rsi.slice(-lookback);
    var pH = findSwingHighs(p);
    var pL = findSwingLows(p);
    var rH = findSwingHighs(r);
    var rL = findSwingLows(r);
    if (pH.length >= 2 && rH.length >= 2) {
      var lPH = pH[pH.length-1], sPH = pH[pH.length-2];
      var lRH = rH[rH.length-1], sRH = rH[rH.length-2];
      if (lPH[1] > sPH[1] && lRH[1] < sRH[1]) {
        return lRH[1] < 60 ? "3-DRIVE BEARISH N-DIV" : "BEARISH DIVERGENCE";
      }
    }
    if (pL.length >= 2 && rL.length >= 2) {
      var lPL = pL[pL.length-1], sPL = pL[pL.length-2];
      var lRL = rL[rL.length-1], sRL = rL[rL.length-2];
      if (lPL[1] < sPL[1] && lRL[1] > sRL[1]) {
        return lRL[1] > 40 ? "3-DRIVE BULLISH P-DIV" : "BULLISH DIVERGENCE";
      }
    }
    return "NO_DIVERGENCE";
  } catch(e) { return "ERROR: " + e.message; }
}

function computeRSI(prices, period) {
  if (prices.length < period + 1) return null;
  var gains = [], losses = [];
  for (var i = 1; i < prices.length; i++) {
    var d = prices[i] - prices[i - 1];
    gains.push(d > 0 ? d : 0);
    losses.push(d < 0 ? -d : 0);
  }
  var ag = gains.slice(0, period).reduce(function(a, b) { return a + b; }, 0) / period;
  var al = losses.slice(0, period).reduce(function(a, b) { return a + b; }, 0) / period;
  var rsi = [];
  for (var i = period; i < gains.length; i++) {
    ag = (ag * (period - 1) + gains[i]) / period;
    al = (al * (period - 1) + losses[i]) / period;
    var rs = al === 0 ? 100 : ag / al;
    rsi.push(100 - (100 / (1 + rs)));
  }
  return rsi;
}

function findSwingHighs(arr) {
  var h = [];
  for (var i = 2; i < arr.length - 2; i++)
    if (arr[i] > arr[i-1] && arr[i] > arr[i-2] && arr[i] > arr[i+1] && arr[i] > arr[i+2])
      h.push([i, arr[i]]);
  return h;
}

function findSwingLows(arr) {
  var l = [];
  for (var i = 2; i < arr.length - 2; i++)
    if (arr[i] < arr[i-1] && arr[i] < arr[i-2] && arr[i] < arr[i+1] && arr[i] < arr[i+2])
      l.push([i, arr[i]]);
  return l;
}

function refreshAllRSI() {
  setup_RSI_Columns();
  SpreadsheetApp.getActiveSpreadsheet().toast("RSI refreshed!", "Done");
}
