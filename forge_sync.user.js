// ==UserScript==
// @name         ぷろんぷたん Forge連携
// @namespace    http://tampermonkey.net/
// @version      1.3
// @description  Forgeの設定をぷろんぷたんに送る＆ぷろんぷたんのプロンプトをForgeに自動入力！
// @author       kofude
// @match        http://127.0.0.1:7860/*
// @match        http://127.0.0.1:7861/*
// @match        http://localhost:7860/*
// @match        http://localhost:7861/*
// @grant        GM_xmlhttpRequest
// @connect      127.0.0.1
// @connect      localhost
// ==/UserScript==

(function () {
    'use strict';

    // ぷろんぷたんのポート範囲（7871〜7880を順番に試す）
    const PORT_START = 7871;
    const PORT_END   = 7880;
    const AUTO_KEY   = 'puromputan_auto_fill';   // 自動入力ON/OFFの保存キー
    let puromputan_port = null;
    let lastSeq   = -1;      // 最後に取り込んだプロンプトの番号
    let baselined = false;   // ページ読込直後の古いプロンプトを取り込まないための基準化フラグ

    // ── ぷろんぷたんのポートを自動探索 ──────────
    function findPuromputan(callback) {
        let port = PORT_START;
        function tryNext() {
            if (port > PORT_END) {
                console.warn('[ぷろんぷたん Forge連携] ぷろんぷたんが見つからなかった！起動してるか確認してね。');
                showStatus('❌ ぷろんぷたんが見つからなかった！', 'red');
                return;
            }
            GM_xmlhttpRequest({
                method:  'GET',
                url:     `http://127.0.0.1:${port}/config`,
                timeout: 500,
                onload: function() {
                    console.log(`[ぷろんぷたん Forge連携] ポート${port}で発見！`);
                    puromputan_port = port;
                    callback(port);
                },
                onerror: function() { port++; tryNext(); },
                ontimeout: function() { port++; tryNext(); }
            });
        }
        tryNext();
    }

    // ── UI（右下のボタン列）─────────────────────
    const BTN_CSS = `
        background: linear-gradient(135deg, #ffb3cc, #a8d8ff);
        color: #3a3a3a;
        border: none;
        border-radius: 24px;
        padding: 10px 18px;
        font-size: 13px;
        font-weight: bold;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        transition: transform 0.1s;
    `;

    function addUI() {
        const wrap = document.createElement('div');
        wrap.style.cssText = `
            position: fixed; bottom: 24px; right: 24px; z-index: 99999;
            display: flex; flex-direction: column; gap: 8px; align-items: flex-end;
        `;
        document.body.appendChild(wrap);

        // ステータス表示
        const lbl = document.createElement('div');
        lbl.id = 'puromputan-status';
        lbl.style.cssText = `
            background: rgba(255,255,255,0.95); color: #3a3a3a;
            border-radius: 12px; padding: 6px 14px; font-size: 12px;
            display: none; box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        `;
        wrap.appendChild(lbl);

        // 自動入力トグル
        const auto = document.createElement('label');
        auto.style.cssText = `
            background: rgba(255,255,255,0.95); color: #3a3a3a;
            border-radius: 18px; padding: 7px 14px; font-size: 12px; font-weight: bold;
            cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            display: flex; align-items: center; gap: 6px;
        `;
        const chk = document.createElement('input');
        chk.type = 'checkbox';
        chk.checked = (localStorage.getItem(AUTO_KEY) ?? '1') === '1';   // 初期値ON
        chk.onchange = () => {
            localStorage.setItem(AUTO_KEY, chk.checked ? '1' : '0');
            showStatus(chk.checked ? '🔄 自動入力ON！届いたら反映するよ' : '⏸ 自動入力OFF', '#1565c0');
        };
        auto.appendChild(chk);
        auto.appendChild(document.createTextNode('🪄 自動入力（届いたら反映）'));
        wrap.appendChild(auto);

        // 手動取り込みボタン
        const pullBtn = document.createElement('button');
        pullBtn.textContent = '📥 ぷろんぷたんから取り込む';
        pullBtn.style.cssText = BTN_CSS;
        pullBtn.onmouseenter = () => pullBtn.style.transform = 'scale(1.05)';
        pullBtn.onmouseleave = () => pullBtn.style.transform = 'scale(1.0)';
        pullBtn.onclick = () => pullPrompt(true);
        wrap.appendChild(pullBtn);

        // 設定送信ボタン（従来）
        const sendBtn = document.createElement('button');
        sendBtn.textContent = '📤 ぷろんぷたんに設定を送る！';
        sendBtn.style.cssText = BTN_CSS;
        sendBtn.onmouseenter = () => sendBtn.style.transform = 'scale(1.05)';
        sendBtn.onmouseleave = () => sendBtn.style.transform = 'scale(1.0)';
        sendBtn.onclick = sendSettings;
        wrap.appendChild(sendBtn);
    }

    function showStatus(msg, color) {
        const lbl = document.getElementById('puromputan-status');
        if (!lbl) return;
        lbl.textContent = msg;
        lbl.style.color = color || '#3a3a3a';
        lbl.style.display = 'block';
        setTimeout(() => lbl.style.display = 'none', 3000);
    }

    // ── Forge → ぷろんぷたん（設定送信・従来機能）──
    function readSettings() {
        function valById(id) {
            const el = document.querySelector(`#${id} input`);
            return el ? el.value : null;
        }
        function findSampler() {
            const el = document.querySelector('#txt2img_sampling input, #sampler_name input');
            return el ? el.value : null;
        }
        return {
            steps:   valById('txt2img_steps'),
            cfg:     valById('txt2img_cfg_scale'),
            width:   valById('txt2img_width'),
            height:  valById('txt2img_height'),
            sampler: findSampler(),
        };
    }

    function sendSettings() {
        const doSend = (port) => {
            const s = readSettings();
            console.log('[ぷろんぷたん Forge連携] 読み取った設定:', s);
            GM_xmlhttpRequest({
                method:  'POST',
                url:     `http://127.0.0.1:${port}/settings`,
                headers: { 'Content-Type': 'application/json' },
                data:    JSON.stringify(s),
                onload:  (res) => {
                    if (res.status === 200) showStatus('✅ ぷろんぷたんに送ったよ！', '#2e7d32');
                    else showStatus('❌ 送信失敗…', 'red');
                },
                onerror: () => showStatus('❌ 送信失敗！ぷろんぷたんが起動してるか確認してね', 'red'),
            });
        };
        if (puromputan_port) doSend(puromputan_port);
        else { showStatus('🔍 ぷろんぷたんを探してるよ…', '#1565c0'); findPuromputan(doSend); }
    }

    // ── ぷろんぷたん → Forge（プロンプト自動入力・新機能）──
    function fillPrompts(pos, neg) {
        const posTa = document.querySelector('#txt2img_prompt textarea');
        const negTa = document.querySelector('#txt2img_neg_prompt textarea');
        if (!posTa) return false;
        const setVal = (ta, v) => {
            if (!ta || v == null) return;
            ta.value = v;
            // Gradioに変更を認識させる
            ta.dispatchEvent(new Event('input',  { bubbles: true }));
            ta.dispatchEvent(new Event('change', { bubbles: true }));
        };
        setVal(posTa, pos);
        setVal(negTa, neg);
        return true;
    }

    function pullPrompt(manual) {
        const doPull = (port) => {
            GM_xmlhttpRequest({
                method:  'GET',
                url:     `http://127.0.0.1:${port}/prompt`,
                timeout: 1500,
                onload: (res) => {
                    let d;
                    try { d = JSON.parse(res.responseText); } catch (e) { return; }
                    if (manual) {
                        lastSeq = d.seq; baselined = true;
                        if (!d.positive) { showStatus('📭 まだプロンプトが無いみたい', '#9a8fa6'); return; }
                        if (fillPrompts(d.positive, d.negative || ''))
                            showStatus('📥 プロンプトを取り込んだよ！', '#2e7d32');
                        return;
                    }
                    // 自動：初回は基準化だけ（ページを開いた瞬間に古いのを流し込まない）
                    if (!baselined) { lastSeq = d.seq; baselined = true; return; }
                    if (d.seq !== lastSeq && d.positive) {
                        lastSeq = d.seq;
                        if (fillPrompts(d.positive, d.negative || ''))
                            showStatus('🪄 新しいプロンプトを自動入力したよ！', '#2e7d32');
                    }
                },
            });
        };
        if (puromputan_port) doPull(puromputan_port);
        else if (manual) { showStatus('🔍 ぷろんぷたんを探してるよ…', '#1565c0'); findPuromputan(doPull); }
    }

    // 自動入力ポーリング（2秒ごと・トグルONのときだけ）
    setInterval(() => {
        if ((localStorage.getItem(AUTO_KEY) ?? '1') === '1') pullPrompt(false);
    }, 2000);

    if (document.readyState === 'complete') {
        setTimeout(addUI, 1500);
    } else {
        window.addEventListener('load', () => setTimeout(addUI, 1500));
    }

    // ページ読み込み時にポートを事前に探しておく
    setTimeout(() => findPuromputan(() => {}), 2000);

})();
