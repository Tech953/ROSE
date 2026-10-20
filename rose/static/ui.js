'use strict';
window.RoseUI=(()=>{
 const get=id=>document.getElementById(id);
 const storage=(kind,method,key,value)=>{try{return window[kind][method](key,value);}catch{return null;}};
 const read=(kind,key)=>storage(kind,'getItem',key);
 const write=(kind,key,value)=>{try{window[kind].setItem(key,value);return true;}catch{return false;}};
 const remove=(kind,key)=>storage(kind,'removeItem',key);
 function validSession(s){return !!s&&/^\w{8}$/.test(s.code)&&typeof s.id==='string'&&!!s.id&&typeof s.token==='string'&&!!s.token&&s.token.length<=512;}
 function session(kind){const raw=read(kind,'rose-session');if(!raw)return null;try{const s=JSON.parse(raw);if(!validSession(s))throw Error();return s;}catch{remove(kind,'rose-session');return null;}}
 const key=(node,value)=>{node.dataset.uiKey=value;return node;};
 let pendingFocus=null;
 function remember(){const entries=new Map();for(const n of document.querySelectorAll('[data-ui-key]'))entries.set(n.dataset.uiKey,{open:n.open,value:n.tagName==='SELECT'&&n.dataset.restoreValue!=='false'?n.value:undefined});const focused=document.activeElement;return {entries,focus:focused?.dataset.uiKey,focusId:focused?.id,focused};}
 function restore(saved){let focus=null;for(const n of document.querySelectorAll('[data-ui-key]')){const prior=saved.entries.get(n.dataset.uiKey);if(prior){if(n.tagName==='DETAILS')n.open=prior.open;if(prior.value!==undefined&&Array.from(n.children).some(o=>o.value===prior.value))n.value=prior.value;}if(n.dataset.uiKey===saved.focus)focus=n;}if(!saved.focus&&saved.focusId)focus=get(saved.focusId);if(focus&&focus!==saved.focused){if(!focus.disabled)focus.focus({preventScroll:true});else pendingFocus=focus;}}
 function options(select,values){const existing=Array.from(select.children);if(existing.length===values.length&&existing.every((o,i)=>o.value===values[i][1]&&o.textContent===values[i][0]))return;const old=select.value;select.replaceChildren(...values.map(([label,value])=>new Option(label,value)));if(values.some(v=>v[1]===old))select.value=old;}
 function rule(button,reason=''){button.dataset.blockReason=reason;button.title=reason;button.setAttribute('aria-disabled',String(!!reason));}
 function locks(busy){const local=new Set(['crt','disconnect','toggle-grid','toggle-links','stop-route','world-cartography','cursor-move','cursor-interact','cursor-target','toggle-reveal','toggle-occlusion','field-context','field-menu-close','field-menu-look','field-menu-use','field-menu-item','field-menu-skill','field-audio']);for(const b of document.querySelectorAll('button')){b.disabled=!!b.dataset.blockReason||(busy&&!local.has(b.id));b.setAttribute('aria-disabled',String(b.disabled));}get('game').setAttribute('aria-busy',String(busy));if(!busy&&pendingFocus){if(!pendingFocus.disabled&&pendingFocus.isConnected&&document.activeElement===document.body)pendingFocus.focus({preventScroll:true});pendingFocus=null;}}
 return {read,write,remove,session,validSession,key,remember,restore,options,rule,locks};
})();
