// Gemini Assistant - Vanilla JS frontend
(function(){
  const HISTORY_KEY = 'gemini_chat_history_v1';
  const THEME_KEY = 'gemini_theme_v1';

  const els = {
    messages: document.getElementById('messages'),
    input: document.getElementById('input'),
    sendBtn: document.getElementById('sendBtn'),
    clearBtn: document.getElementById('clearChat'),
    themeToggle: document.getElementById('themeToggle'),
    styleSelect: document.getElementById('styleSelect')
  };

  let isLoading = false;
  let history = [];
  let currentUtterance = null;
  let currentSpeakingId = null;

  function init(){
    bindUI();
    loadTheme();
    loadHistory();
    renderHistory();
    autosize();
    loadStyles();
  }

  function bindUI(){
    els.sendBtn.addEventListener('click', handleSend);
    els.input.addEventListener('keydown', handleKeydown);
    els.clearBtn.addEventListener('click', handleClear);
    els.themeToggle.addEventListener('change', toggleTheme);
    if(els.styleSelect) els.styleSelect.addEventListener('change', handleStyleChange);
    els.messages.addEventListener('click', (e)=>{
      // delegate: copy, play, pause, stop
      const btn = e.target.closest('[data-action]');
      if(!btn) return;
      const action = btn.dataset.action;
      const id = btn.closest('.message')?.dataset.id;
      if(!id) return;
      const msg = history.find(m=>m.id===id);
      if(!msg) return;
      if(action==='copy') copyText(msg.text, btn);
      if(action==='play') playSpeech(id,msg.text);
      if(action==='pause') pauseSpeech();
      if(action==='stop') stopSpeech();
    });
    window.addEventListener('beforeunload', ()=>saveHistory());
    els.input.addEventListener('input', autosize);
  }

  function autosize(){
    const ta = els.input;
    ta.style.height = 'auto';
    ta.style.height = Math.min(160, ta.scrollHeight) + 'px';
  }

  function handleKeydown(e){
    if(e.key === 'Enter' && !e.shiftKey){
      e.preventDefault();
      handleSend();
    }
  }

  async function handleSend(){
    const text = els.input.value.trim();
    if(!text || isLoading) return;
    appendLocalMessage('user', text);
    els.input.value=''; autosize();
    try{
      isLoading = true; updateSendState();
      const typingId = showTyping();
      const aiText = await postToBackend(text);
      removeTyping(typingId);
      appendLocalMessage('ai', aiText);
    }catch(err){
      removeTyping();
      appendLocalMessage('ai', 'Error: '+(err.message||'Network error'));
    }finally{
      isLoading = false; updateSendState();
    }
  }

  function updateSendState(){
    els.sendBtn.disabled = isLoading;
  }

  function appendLocalMessage(role, text){
    const msg = {id: genId(), role, text, time: new Date().toISOString()};
    history.push(msg);
    saveHistory();
    const el = createMessageElement(msg);
    els.messages.appendChild(el);
    requestAnimationFrame(()=>el.classList.add('fade-in'));
    scrollToBottom();
    return msg.id;
  }

  function createMessageElement(msg){
    const el = document.createElement('div');
    el.className = 'message '+(msg.role==='user'?'user':'ai');
    el.dataset.id = msg.id;

    const bubble = document.createElement('div');
    bubble.className='msg-bubble';
    bubble.textContent = msg.text;
    el.appendChild(bubble);

    const meta = document.createElement('div');
    meta.className='meta';
    meta.innerHTML = `<span>${formatTime(msg.time)}</span>`;
    el.appendChild(meta);

    if(msg.role==='ai'){
      const actions = document.createElement('div');
      actions.className='actions';
      // speaker controls
      const play = createAction('play','▶');
      const pause = createAction('pause','❚❚');
      const stop = createAction('stop','■');
      const copy = createAction('copy','⧉');
      actions.append(play,pause,stop,copy);
      el.appendChild(actions);
      // hide controls if speech unsupported
      if(!('speechSynthesis' in window)){
        actions.querySelectorAll('[data-action]').forEach(b=>{
          if(b.dataset.action!=='copy') b.style.opacity = '0.35';
          b.title = 'Speech not supported';
        });
      }
    }

    return el;
  }

  function createAction(action, label){
    const b = document.createElement('button');
    b.className='action-btn';
    b.dataset.action = action;
    b.innerText = label;
    b.title = action;
    return b;
  }

  function formatTime(iso){
    try{const d=new Date(iso); return d.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});}catch(e){return ''}
  }

  function genId(){return 'm_'+Math.random().toString(36).slice(2,9)}

  async function postToBackend(message){
    const res = await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message})});
    if(!res.ok){
      const txt = await res.text(); throw new Error(txt || res.statusText);
    }
    const data = await res.json();
    if(typeof data.response !== 'string') throw new Error('Invalid response');
    return data.response;
  }

  function showTyping(){
    const id = genId();
    const el = document.createElement('div');
    el.className='message ai'; el.dataset.id = id;
    const bubble = document.createElement('div'); bubble.className='msg-bubble typing';
    bubble.innerHTML = `<span class="dot"></span><span class="dot"></span><span class="dot"></span>`;
    el.appendChild(bubble);
    els.messages.appendChild(el);
    scrollToBottom();
    return id;
  }

  function removeTyping(id){
    if(id){
      const el = els.messages.querySelector(`.message[data-id="${id}"]`);
      if(el) el.remove();
    } else {
      const el = els.messages.querySelector('.message.ai .typing')?.closest('.message');
      if(el) el.remove();
    }
  }

  function scrollToBottom(){
    els.messages.scrollTo({top: els.messages.scrollHeight, behavior:'smooth'});
  }

  // Speech functions
  function stopSpeech(){
    if('speechSynthesis' in window){
      window.speechSynthesis.cancel();
    }
    if(currentSpeakingId){
      const el = els.messages.querySelector(`.message[data-id="${currentSpeakingId}"]`);
      if(el) el.classList.remove('speaking');
      currentSpeakingId = null; currentUtterance = null;
    }
  }

  function pauseSpeech(){
    if(!('speechSynthesis' in window)) return;
    if(window.speechSynthesis.paused) return;
    window.speechSynthesis.pause();
  }

  function resumeSpeech(){
    if(!('speechSynthesis' in window)) return;
    if(window.speechSynthesis.paused) window.speechSynthesis.resume();
  }

  function playSpeech(id,text){
    if(!('speechSynthesis' in window)) return;
    // stop previous
    stopSpeech();
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = 'en-US';
    utter.rate = 1.0;
    utter.pitch = 1.0;
    utter.onstart = ()=>{
      currentSpeakingId = id; currentUtterance = utter;
      const el = els.messages.querySelector(`.message[data-id="${id}"]`);
      if(el) el.classList.add('speaking');
    };
    utter.onend = ()=>{
      const el = els.messages.querySelector(`.message[data-id="${id}"]`);
      if(el) el.classList.remove('speaking');
      currentSpeakingId = null; currentUtterance = null;
    };
    utter.onerror = ()=>{stopSpeech();};
    window.speechSynthesis.speak(utter);
  }

  function copyText(text, btn){
    if(!navigator.clipboard) return;
    navigator.clipboard.writeText(text).then(()=>{
      btn.textContent = '✓';
      setTimeout(()=>btn.textContent='⧉',700);
    }).catch(()=>{});
  }

  // Persistence
  function saveHistory(){
    try{localStorage.setItem(HISTORY_KEY, JSON.stringify(history));}catch(e){}
  }
  function loadHistory(){
    try{const raw = localStorage.getItem(HISTORY_KEY); history = raw?JSON.parse(raw):[];}catch(e){history=[]}
  }

  function renderHistory(){
    els.messages.innerHTML='';
    for(const m of history){
      const el = createMessageElement({id:m.id, role:m.role==='user'?'user':'ai', text:m.text, time:m.time});
      els.messages.appendChild(el);
      el.classList.add('fade-in');
    }
    scrollToBottom();
  }

  function handleClear(){
    if(!confirm('Clear chat history?')) return;
    history = [];
    saveHistory();
    renderHistory();
  }

  function toggleTheme(){
    const isLight = els.themeToggle.checked;
    document.body.classList.toggle('light', isLight);
    try{localStorage.setItem(THEME_KEY, isLight? 'light':'dark');}catch(e){}
  }

  async function loadStyles(){
    if(!els.styleSelect) return;
    try {
      const res = await fetch('/styles');
      const styles = await res.json();
      els.styleSelect.innerHTML = '';
      for (const [key, style] of Object.entries(styles)) {
        const opt = document.createElement('option');
        opt.value = key;
        opt.textContent = style.name;
        if (key === '4') opt.selected = true;
        els.styleSelect.appendChild(opt);
      }
    } catch(e) {
      console.error('Failed to load styles', e);
    }
  }

  async function handleStyleChange() {
    if(!els.styleSelect) return;
    const styleId = els.styleSelect.value;
    try {
      const res = await fetch('/init', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ style_id: styleId })
      });
      if (!res.ok) throw new Error('Failed to initialize chat');
      history = [];
      saveHistory();
      renderHistory();
      const data = await res.json();
      appendLocalMessage('ai', 'Chat restarted with ' + data.style + ' style.');
    } catch(e) {
      console.error(e);
      appendLocalMessage('ai', 'Error changing style: ' + e.message);
    }
  }

  function loadTheme(){
    try{
      const t = localStorage.getItem(THEME_KEY);
      const isLight = t === 'light';
      els.themeToggle.checked = isLight;
      document.body.classList.toggle('light', isLight);
    }catch(e){}
  }

  // initialize
  init();

  // expose some functions for debugging
  window.gemini = {playSpeech, pauseSpeech, stopSpeech, history};

})();
