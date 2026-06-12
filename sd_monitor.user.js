// ==UserScript==
// @name         ぷろんぷたん 連携スクリプト
// @namespace    http://tampermonkey.net/
// @version      2.0
// @description  AIチャットでSDプロンプトを検知してぷろんぷたんに自動送信するよ！
// @author       kofude
// @match        https://claude.ai/*
// @match        https://chat.openai.com/*
// @match        https://chatgpt.com/*
// @match        https://gemini.google.com/*
// @match        https://grok.x.com/*
// @match        https://grok.com/*
// @match        https://copilot.microsoft.com/*
// @grant        GM_xmlhttpRequest
// @connect      127.0.0.1
// @connect      localhost
// ==/UserScript==

(function () {
    'use strict';

    const PORT_START = 7871;
    const PORT_END   = 7880;
    let puromputan_port = null;
    let retryInterval   = null;
    let checkTimeout    = null;

    let POS_START = '🔴';
    let POS_END   = '🟥';
    let NEG_START = '🔵';
    let NEG_END   = '🟦';

    // sessionStorage でリロード後も重複送信を防ぐ
    function getLastKey() { return sessionStorage.getItem('puromputan_lastKey') || ''; }
    function setLastKey(k) { sessionStorage.setItem('puromputan_lastKey', k); }

    // ── ポート自動探索 ─────────────────────────
    function findPuromputan(callback) {
        let port = PORT_START;
        function tryNext() {
            if (port > PORT_END) {
                console.warn('[ぷろんぷたん] 見つからなかった！15秒後にリトライするよ。');
                return;
            }
            GM_xmlhttpRequest({
                method: 'GET', url: `http://127.0.0.1:${port}/config`, timeout: 800,
                onload: function(res) {
                    puromputan_port = port;
                    if (retryInterval) { clearInterval(retryInterval); retryInterval = null; }
                    try {
                        const cfg = JSON.parse(res.responseText);
                        if (cfg.pos_start) POS_START = cfg.pos_start;
                        if (cfg.pos_end)   POS_END   = cfg.pos_end;
                        if (cfg.neg_start) NEG_START = cfg.neg_start;
                        if (cfg.neg_end)   NEG_END   = cfg.neg_end;
                        console.log(`[ぷろんぷたん] ポート${port}で発見！マーカー: ${POS_START}〜${POS_END} / ${NEG_START}〜${NEG_END}`);
                    } catch(e) { console.warn('[ぷろんぷたん] config parse error:', e); }
                    if (callback) callback();
                },
                onerror:   function() { port++; tryNext(); },
                ontimeout: function() { port++; tryNext(); }
            });
        }
        tryNext();
    }

    function startRetryLoop() {
        if (retryInterval) return;
        retryInterval = setInterval(function() {
            if (!puromputan_port) {
                console.log('[ぷろんぷたん] リトライ中...');
                findPuromputan(null);
            }
        }, 15000);
    }

    // ── プロンプト切り出し ────────────────────
    function extractBetween(text, start, end) {
        const endPos = text.lastIndexOf(end);
        if (endPos === -1) return null;
        const startPos = text.lastIndexOf(start, endPos - 1);
        if (startPos === -1) return null;
        return text.slice(startPos + start.length, endPos).trim();
    }

    // ── プロンプト検知＆送信 ──────────────────
    function checkForPrompts() {
        if (!puromputan_port) return;

        const scanText = (document.body.innerText || '').slice(-10000);

        // ── ポジを探す ──────────────────────────────
        const posEndPos   = scanText.lastIndexOf(POS_END);
        if (posEndPos === -1) return;
        const posStartPos = scanText.lastIndexOf(POS_START, posEndPos - 1);
        if (posStartPos === -1) return;
        const positive = scanText.slice(posStartPos + POS_START.length, posEndPos).trim();
        if (!positive) return;
        // 短すぎるプロンプトはスルー（10文字未満は誤検知とみなす）
        if (positive.length < 10) return;

        // ── ネガはポジの「後」にあるものだけ有効 ──
        // ポジより前にある古いネガを拾わないようにする
        const textAfterPos = scanText.slice(posEndPos);
        const negEndPos    = textAfterPos.lastIndexOf(NEG_END);
        let negative = null;
        if (negEndPos !== -1) {
            const negStartPos = textAfterPos.lastIndexOf(NEG_START, negEndPos - 1);
            if (negStartPos !== -1) {
                negative = textAfterPos.slice(negStartPos + NEG_START.length, negEndPos).trim() || null;
            }
        }

        const key = positive + '|||' + (negative || '');
        if (key === getLastKey()) return;
        setLastKey(key);

        if (negative) {
            console.log('[ぷろんぷたん] ポジ＆ネガ発見！送信します。');
            send({ positive, negative });
        } else {
            console.log('[ぷろんぷたん] ポジのみ発見！送信します。');
            send({ positive, negative: '' });
        }
    }

    function send(data) {
        GM_xmlhttpRequest({
            method:  'POST',
            url:     `http://127.0.0.1:${puromputan_port}/prompt`,
            headers: { 'Content-Type': 'application/json' },
            data:    JSON.stringify(data),
            onload:  (r) => console.log('[ぷろんぷたん] 送信成功！ status:', r.status),
            onerror: () => {
                console.warn('[ぷろんぷたん] 送信失敗。再探索します。');
                puromputan_port = null;
                startRetryLoop();
                findPuromputan(null);
            }
        });
    }

    // ── DOM監視（2秒デバウンス）─────────────
    const observer = new MutationObserver(function() {
        clearTimeout(checkTimeout);
        checkTimeout = setTimeout(checkForPrompts, 2000);
    });

    observer.observe(document.body, { childList: true, subtree: true });
    findPuromputan(null);
    startRetryLoop();
    console.log('[ぷろんぷたん] v2.0 監視スタート！');

})();
