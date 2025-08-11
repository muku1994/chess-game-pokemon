<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Pokémon Chess — Canvas</title>
  <style>
    :root{
      --bg:#f0fff5;
      --cell-dark:#a8d5ba;
      --cell-light:#d4f0d7;
      --ui:#16301a;
      --accent-yellow:#ffd166;
      --accent-danger:#ff3864;
    }
    html,body{height:100%;margin:0;background:var(--bg);font-family:system-ui,Segoe UI,Roboto,Inter,Helvetica,Arial,sans-serif;color:var(--ui)}
    .wrap{display:grid;place-items:center;height:100%;gap:16px;padding:16px}
    .hud{display:flex;gap:12px;align-items:center;flex-wrap:wrap;justify-content:center}
    .badge{padding:.35rem .6rem;border-radius:999px;background:#fff;color:#2b5132;font-size:.85rem}
    .btn{border:0;background:#e6ffee;color:#224828;padding:.55rem .9rem;border-radius:12px;cursor:pointer;box-shadow:0 2px 0 #b9e0c3;transition:transform .06s ease}
    .btn:hover{transform:translateY(-1px)}
    .btn:active{transform:translateY(0)}
    canvas{background:linear-gradient(135deg,var(--cell-dark),var(--cell-light));box-shadow:0 12px 35px rgba(0,0,0,.25);border-radius:16px}
    .legend{opacity:.8;font-size:.9rem}
    .title{font-weight:700;letter-spacing:.3px}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="title">♟️ Pokémon Chess — <span class="legend">HTML5 Canvas</span></div>
    <canvas id="board" width="672" height="672"></canvas>
    <div class="hud">
      <span class="badge" id="turnBadge">Turn: <strong style="color:red">Red</strong> (Trainers)</span>
      <span class="badge" id="status"></span>
      <button class="btn" id="undoBtn" title="Undo (U)">Undo</button>
      <button class="btn" id="resetBtn" title="Reset (R)">Reset</button>
      <button class="btn" id="flipBtn" title="Flip board (F)">Flip</button>
    </div>
  </div>

  <script>
  'use strict';
  // Wrap everything to avoid dangling syntax and guarantee closure
  (function(){
    // === Chess engine (wired to Pokémon sprites) ===
    const EMPTY = 0;
    const S = { G:8, P:16 };          // G = Red (Trainers), P = Purple (Team Rocket)
    const T = { P:1, N:2, B:3, R:4, Q:5, K:6 };

    function piece(side, type){ return side | type; }
    function sideOf(p){ return p & 24; }
    function typeOf(p){ return p & 7; }

    const START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

    function parseFEN(fen){
      const [pieceRows, turn, castling, ep] = fen.split(' ');
      const rows = pieceRows.split('/');
      const board = Array(64).fill(EMPTY);
      for(let r=0; r<8; r++){
        let c=0;
        for(const ch of rows[7-r]){ // FEN is 8..1
          if(/[1-8]/.test(ch)){
            c += +ch;
          } else {
            const isUpper = ch === ch.toUpperCase();
            const side = isUpper ? S.G : S.P;
            const map = { p:T.P, n:T.N, b:T.B, r:T.R, q:T.Q, k:T.K };
            board[r*8 + c] = piece(side, map[ch.toLowerCase()]);
            c++;
          }
        }
      }
      return {
        board,
        turn: turn === 'w' ? S.G : S.P,
        castling,
        ep: ep === '-' ? -1 : algebraToIndex(ep)
      };
    }

    function cloneState(s){ return { board: s.board.slice(), turn: s.turn, castling: s.castling, ep: s.ep }; }
    function indexToRC(i){ return [i>>3, i&7]; }
    function rcToIndex(r,c){ return (r<<3) | c; }
    function inBoard(r,c){ return r>=0 && r<8 && c>=0 && c<8; }
    function algebraToIndex(a){ const f=a.charCodeAt(0)-97, r=a.charCodeAt(1)-49; return rcToIndex(r,f); }
    function indexToAlgebra(i){ const [r,c]=indexToRC(i); return String.fromCharCode(97+c)+(1+r); }

    const DIR = {
      N: [[1,0]],
      B: [[1,1],[1,-1],[-1,1],[-1,-1]],
      R: [[1,0],[-1,0],[0,1],[0,-1]],
      Q: [[1,1],[1,-1],[-1,1],[-1,-1],[1,0],[-1,0],[0,1],[0,-1]],
      K: [[1,1],[1,-1],[-1,1],[-1,-1],[1,0],[-1,0],[0,1],[0,-1]],
      N2: [[2,1],[2,-1],[-2,1],[-2,-1],[1,2],[1,-2],[-1,2],[-1,-2]]
    };

    function generateMoves(state){
      const { board, turn } = state;
      const moves = [];
      for(let i=0;i<64;i++){
        const p = board[i];
        if(!p || sideOf(p)!==turn) continue;
        const t = typeOf(p);
        const [r,c] = indexToRC(i);
        if(t===T.P){
          const dir = turn===S.G ? 1 : -1;
          const startRank = turn===S.G ? 1 : 6;
          const r1 = r+dir;
          if(inBoard(r1,c) && board[rcToIndex(r1,c)]===EMPTY){
            moves.push({from:i,to:rcToIndex(r1,c),pawn:1});
            if(r===startRank){
              const r2 = r+2*dir;
              if(board[rcToIndex(r2,c)]===EMPTY) moves.push({from:i,to:rcToIndex(r2,c),pawn:1,double:1});
            }
          }
          for(const dc of [-1,1]){
            const rr=r+dir, cc=c+dc;
            if(inBoard(rr,cc)){
              const j=rcToIndex(rr,cc);
              if(board[j]!==EMPTY && sideOf(board[j])!==turn) moves.push({from:i,to:j,cap:1,pawn:1});
              if(j===state.ep) moves.push({from:i,to:j,ep:1,pawn:1});
            }
          }
        } else if(t===T.N){
          for(const [dr,dc] of DIR.N2){
            const rr=r+dr, cc=c+dc; if(!inBoard(rr,cc)) continue; const j=rcToIndex(rr,cc); if(sideOf(board[j])!==turn) moves.push({from:i,to:j});
          }
        } else if(t===T.B || t===T.R || t===T.Q){
          const vecs = t===T.B?DIR.B : t===T.R?DIR.R : DIR.Q;
          for(const [dr,dc] of vecs){
            let rr=r+dr, cc=c+dc;
            while(inBoard(rr,cc)){
              const j = rcToIndex(rr,cc);
              if(board[j]===EMPTY){ moves.push({from:i,to:j}); }
              else { if(sideOf(board[j])!==turn) moves.push({from:i,to:j}); break; }
              rr+=dr; cc+=dc;
            }
          }
        } else if(t===T.K){
          for(const [dr,dc] of DIR.K){ const rr=r+dr, cc=c+dc; if(!inBoard(rr,cc)) continue; const j=rcToIndex(rr,cc); if(sideOf(board[j])!==turn) moves.push({from:i,to:j}); }
          const rights = state.castling;
          const meRed = turn===S.G;
          const canK = rights.includes(meRed? 'K':'k');
          const canQ = rights.includes(meRed? 'Q':'q');
          const homeR = meRed?0:7;
          const kingFrom = rcToIndex(meRed?0:7,4);
          if(i===kingFrom && !inCheck(state,turn)){
            if(canK && board[rcToIndex(homeR,5)]===EMPTY && board[rcToIndex(homeR,6)]===EMPTY){
              const st1 = makeMove(cloneState(state), {from:i,to:rcToIndex(homeR,5),castleProbe:1});
              if(!inCheck(st1,turn)){
                const st2 = makeMove(cloneState(state), {from:i,to:rcToIndex(homeR,6),castleProbe:1});
                if(!inCheck(st2,turn)) moves.push({from:i,to:rcToIndex(homeR,6),castle:'K'});
              }
            }
            if(canQ && board[rcToIndex(homeR,3)]===EMPTY && board[rcToIndex(homeR,2)]===EMPTY && board[rcToIndex(homeR,1)]===EMPTY){
              const st1 = makeMove(cloneState(state), {from:i,to:rcToIndex(homeR,3),castleProbe:1});
              if(!inCheck(st1,turn)){
                const st2 = makeMove(cloneState(state), {from:i,to:rcToIndex(homeR,2),castleProbe:1});
                if(!inCheck(st2,turn)) moves.push({from:i,to:rcToIndex(homeR,2),castle:'Q'});
              }
            }
          }
        }
      }
      // filter illegal
      const legal=[];
      for(const m of moves){ const st=makeMove(cloneState(state), m); if(!inCheck(st, state.turn)) legal.push(m); }
      return legal;
    }

    function makeMove(state, move){
      const b=state.board, turn=state.turn; const opp=turn===S.G?S.P:S.G;
      const p=b[move.from]; const t=typeOf(p);
      if(move.ep){ const [rto,cto]=indexToRC(move.to); const capIdx = rcToIndex(rto + (turn===S.G?-1:1), cto); b[capIdx]=EMPTY; }
      b[move.to]=b[move.from]; b[move.from]=EMPTY;
      if(t===T.P){ const [rto]=indexToRC(move.to); if(rto===7 && turn===S.G){ b[move.to]=piece(S.G,T.Q); } if(rto===0 && turn===S.P){ b[move.to]=piece(S.P,T.Q); } }
      state.ep = -1; if(move.double){ const [r,c]=indexToRC(move.to); state.ep = rcToIndex(r + (turn===S.G?-1:1), c); }
      if(move.castle && !move.castleProbe){ const meRed = turn===S.G; const row = meRed?0:7; if(move.castle==='K'){ const rookFrom = rcToIndex(row,7), rookTo=rcToIndex(row,5); b[rookTo]=b[rookFrom]; b[rookFrom]=EMPTY; } else { const rookFrom = rcToIndex(row,0), rookTo=rcToIndex(row,3); b[rookTo]=b[rookFrom]; b[rookFrom]=EMPTY; } }
      const lose = me => { state.castling = state.castling.replace(me,''); };
      const fromAlg=indexToAlgebra(move.from), toAlg=indexToAlgebra(move.to);
      if(t===T.K){ if(turn===S.G){ lose('K'); lose('Q'); } else { lose('k'); lose('q'); } }
      if(fromAlg==='h1'||toAlg==='h1') lose('K'); if(fromAlg==='a1'||toAlg==='a1') lose('Q');
      if(fromAlg==='h8'||toAlg==='h8') lose('k'); if(fromAlg==='a8'||toAlg==='a8') lose('q');
      state.turn = opp; return state;
    }

    function kingIndex(board, side){ const target=piece(side,T.K); for(let i=0;i<64;i++) if(board[i]===target) return i; return -1; }

    function rawAttacks(state){
      const {board,turn} = state;
      const moves=[];
      for(let i=0;i<64;i++){
        const p=board[i]; if(!p||sideOf(p)!==turn) continue; const t=typeOf(p); const [r,c]=indexToRC(i);
        if(t===T.P){
          const dir=turn===S.G?1:-1;
          for(const dc of [-1,1]){
            const rr=r+dir, cc=c+dc; if(inBoard(rr,cc)){ const j=rcToIndex(rr,cc); moves.push({from:i,to:j}); }
          }
        } else if(t===T.N){
          for(const [dr,dc] of DIR.N2){ const rr=r+dr, cc=c+dc; if(inBoard(rr,cc)){ const j=rcToIndex(rr,cc); if(sideOf(board[j])!==turn) moves.push({from:i,to:j}); } }
        } else if(t===T.B || t===T.R || t===T.Q){
          const vecs = t===T.B?DIR.B : t===T.R?DIR.R : DIR.Q;
          for(const [dr,dc] of vecs){ let rr=r+dr, cc=c+dc; while(inBoard(rr,cc)){ const j=rcToIndex(rr,cc); if(board[j]===EMPTY){ moves.push({from:i,to:j}); } else { if(sideOf(board[j])!==turn) moves.push({from:i,to:j}); break; } rr+=dr; cc+=dc; } }
        } else if(t===T.K){
          for(const [dr,dc] of DIR.K){ const rr=r+dr, cc=c+dc; if(inBoard(rr,cc)){ const j=rcToIndex(rr,cc); if(sideOf(board[j])!==turn) moves.push({from:i,to:j}); } }
        }
      }
      return moves;
    }

    function attacksSquare(state, sideAttacking, sq){
      const saveTurn = state.turn;
      state.turn = sideAttacking;
      const moves = rawAttacks(state);
      state.turn = saveTurn;
      for(const m of moves){ if(m.to===sq) return true; }
      return false;
    }

    function inCheck(state, side){
      const k = kingIndex(state.board, side);
      return attacksSquare(state, side===S.G?S.P:S.G, k);
    }

    // === Canvas & sprites ===
    const canvas = document.getElementById('board');
    const ctx = canvas.getContext('2d');
    const CELL = canvas.width/8;

    let baseState = parseFEN(START_FEN); baseState.castling='KQkq';
    let history = [cloneState(baseState)];
    let selected = null;
    let legalMovesCache = [];
    let flipped = false;

    const turnBadge = document.getElementById('turnBadge');
    const statusEl = document.getElementById('status');

    const SPRITE_BASE = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/';
    const ids = { pikachu:25, onix:95, rapidash:78, bulbasaur:1, mewtwo:150, charizard:6, meowth:52, golem:76, arbok:24, gengar:94, mew:151, gyarados:130 };
    const mapping={
      red:{ P:'pikachu', R:'onix', N:'rapidash', B:'bulbasaur', Q:'mewtwo', K:'charizard' },
      purple:{ P:'meowth', R:'golem', N:'arbok', B:'gengar', Q:'mew', K:'gyarados' }
    };
    const letter={1:'P',2:'N',3:'B',4:'R',5:'Q',6:'K'};
    const pieceImages={};

    function spriteUrl(name){ const id = ids[name]; return id ? `${SPRITE_BASE}${id}.png` : `${SPRITE_BASE}${name}.png`; }

    function loadPieces(){
      return new Promise(resolve=>{
        let loaded=0, total=0;
        const onload = ()=>{ loaded++; if(loaded===total) resolve(); };
        for(const side in mapping){
          for(const type in mapping[side]){
            total++;
            const name = mapping[side][type];
            const img = new Image();
            img.crossOrigin='anonymous';
            img.src = spriteUrl(name);
            img.onload = onload;
            img.onerror = onload; // don't block if any 404s
            pieceImages[side+type] = img;
          }
        }
      });
    }

    function getCss(v){ return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); }

    function drawBoard(){
      for(let r=0;r<8;r++){
        for(let c=0;c<8;c++){
          const rr = flipped? 7-r : r;
          const cc = flipped? 7-c : c;
          const x = cc*CELL, y = (7-rr)*CELL;
          ctx.fillStyle = ((r+c)%2) ? getCss('--cell-dark') : getCss('--cell-light');
          ctx.fillRect(x,y,CELL,CELL);
          ctx.strokeStyle = 'rgba(0,0,0,0.06)';
          ctx.strokeRect(x+.5,y+.5,CELL-1,CELL-1);
        }
      }
    }

    function draw(){
      drawBoard();
      const st = current();

      if(selected!=null){
        const legal = legalMovesCache.filter(m=>m.from===selected);
        for(const m of legal){
          const [r,c] = indexToRC(m.to);
          const rr = flipped? 7-r : r;
          const cc = flipped? 7-c : c;
          const x = cc*CELL, y = (7-rr)*CELL;
          ctx.globalAlpha = .95;
          ctx.fillStyle = m.cap||m.ep ? 'rgba(161,106,232,.35)' : 'rgba(255,209,102,.35)';
          ctx.beginPath();
          ctx.arc(x+CELL/2, y+CELL/2, CELL*0.18, 0, Math.PI*2);
          ctx.fill();
          ctx.globalAlpha = 1;
        }
        const [sr,sc] = indexToRC(selected);
        const rr = flipped? 7-sr : sr;
        const cc = flipped? 7-sc : sc;
        const x = cc*CELL, y = (7-rr)*CELL;
        ctx.lineWidth = 3;
        ctx.strokeStyle = 'rgba(255,209,102,.9)';
        ctx.strokeRect(x+2,y+2,CELL-4,CELL-4);
      }

      for(let i=0;i<64;i++){
        const p = st.board[i];
        if(!p) continue;
        const [r,c] = indexToRC(i);
        const rr = flipped? 7-r : r;
        const cc = flipped? 7-c : c;
        const x = cc*CELL, y = (7-rr)*CELL;
        const sideName = sideOf(p)===S.G ? 'red' : 'purple';
        const img = pieceImages[sideName + letter[typeOf(p)]];
        if(img){ ctx.save(); ctx.shadowColor='rgba(0,0,0,.25)'; ctx.shadowBlur=6; ctx.drawImage(img,x+6,y+6,CELL-12,CELL-12); ctx.restore(); }
      }

      const turnSide = current().turn;
      const isChk = inCheck(current(), turnSide);
      const legal = generateMoves(current());
      if(isChk){ statusEl.textContent = 'Check!'; statusEl.style.color = getCss('--accent-danger'); } else { statusEl.textContent = ''; }
      turnBadge.innerHTML = `Turn: <strong style="color:${turnSide===S.G?'red':'purple'}">${turnSide===S.G?'Red':'Purple'}</strong> (${turnSide===S.G?'Trainers':'Team Rocket'})`;
      if(legal.length===0){ if(inCheck(current(), turnSide)){ statusEl.textContent = 'Checkmate! ' + (turnSide===S.G? 'Purple (Team Rocket) win.' : 'Red (Trainers) win.'); } else { statusEl.textContent = 'Stalemate.'; } }
    }

    function current(){ return history[history.length-1]; }

    function squareFromXY(mx,my){
      const c = Math.floor(mx/CELL);
      const r = 7 - Math.floor(my/CELL);
      const rr = flipped? 7-r : r;
      const cc = flipped? 7-c : c;
      return rcToIndex(rr,cc);
    }

    // interactions
    function onClick(e){
      const rect = canvas.getBoundingClientRect();
      const mx=e.clientX-rect.left, my=e.clientY-rect.top;
      const sq = squareFromXY(mx,my);
      const st = current();
      const pieceHere = st.board[sq];
      if(selected==null){
        if(pieceHere && sideOf(pieceHere)===st.turn){ selected=sq; legalMovesCache=generateMoves(st); draw(); }
      } else {
        const legal = legalMovesCache.filter(m=>m.from===selected && m.to===sq);
        if(legal.length){ const st2 = makeMove(cloneState(st), legal[0]); history.push(st2); selected=null; legalMovesCache=[]; draw(); }
        else if(pieceHere && sideOf(pieceHere)===st.turn){ selected=sq; legalMovesCache=generateMoves(st); draw(); }
        else { selected=null; draw(); }
      }
    }

    // Buttons & keys
    function wireUI(){
      canvas.addEventListener('click', onClick);
      document.getElementById('undoBtn').onclick = function(){ if(history.length>1){ history.pop(); selected=null; draw(); } };
      document.getElementById('resetBtn').onclick = function(){ history=[cloneState(parseFEN(START_FEN))]; history[0].castling='KQkq'; selected=null; flipped=false; draw(); };
      document.getElementById('flipBtn').onclick = function(){ flipped=!flipped; draw(); };
      window.addEventListener('keydown', function(e){
        if(e.key==='u'||e.key==='U') document.getElementById('undoBtn').click();
        if(e.key==='r'||e.key==='R') document.getElementById('resetBtn').click();
        if(e.key==='f'||e.key==='F') document.getElementById('flipBtn').click();
      });
    }

    // --- Console tests (do not change existing) ---
    function runTests(){
      console.log('%cRunning built-in tests…','color:#2b5132');
      // 1) Start position: each side has legal moves
      let st = cloneState(parseFEN(START_FEN)); st.castling='KQkq'; console.assert(generateMoves(st).length>0,'Start position should have moves');
      // 2) En passant target set after double pawn move
      const a = cloneState(parseFEN(START_FEN)); a.castling='KQkq';
      const e2 = algebraToIndex('e2'), e4 = algebraToIndex('e4');
      makeMove(a,{from:e2,to:e4,pawn:1,double:1});
      console.assert(a.ep===algebraToIndex('e3'),'EP square should be e3 after e2-e4');
      // 3) Castling availability in empty board scenario
      const fenCastle = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"; let cst = parseFEN(fenCastle); console.assert(generateMoves(cst).some(m=>m.castle==='K'),'K-side castling exists');
      // 4) Board math
      console.assert(indexToAlgebra(algebraToIndex('a1'))==='a1','algebra<->index roundtrip');

      // Additional tests (added without changing originals)
      // 5) Knight has 2 legal moves at start (b1 to a3/c3)
      const start = cloneState(parseFEN(START_FEN)); start.castling='KQkq';
      const b1 = algebraToIndex('b1');
      const moves = generateMoves(start).filter(m=>m.from===b1);
      console.assert(moves.length===2,'Knight at b1 should have 2 moves');
      // 6) No castling through check
      const fenNoCastle = "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1"; let nc = parseFEN(fenNoCastle); // black to move
      // Put a rook attacking f8 to simulate through-check
      nc.board[algebraToIndex('f2')] = piece(S.G,T.R);
      console.assert(!generateMoves(nc).some(m=>m.castle==='K'),'Castling through check should be disallowed');
      console.log('%cTests finished','color:#2b5132');
    }

    // Init
    loadPieces().then(function(){ wireUI(); draw(); runTests(); });
  })();
  </script>
</body>
</html>
