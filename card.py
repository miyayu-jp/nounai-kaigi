"""脳内メーカー・前後カード：会議の前と後の頭の中を並べ、Xに貼れる16:9の1枚にする。
入力は JSON 1ファイル（例は sample_meeting.json）。"""
import sys, math, random, json, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nm_font import FONT
K = 2                      # 内部の拡大率
CW, CH = 1200*K, 675*K     # 出力 1200x675
LOOK = {"感情":("感","circle","#f07272","big"),"理性":("理","pill","#5d9be8","flat"),"不安":("不","hex","#a08ad8","worry"),
        "愛":("愛","drop","#ee86b4","happy"),"めんどくさい":("面","squircle","#8a9bb0","sleepy"),"ツッコミ":("ツ","circle","#eaa04a","angry"),
        "ボケ":("ボ","drop","#d8b72e","wink"),"議長":("議","hex","#6cb85c","normal"),"ミライ":("ミ","circle","#2EB3A3","normal"),"お金":("金","squircle","#e8c440","normal"),"時間":("時","pill","#3cb4e6","normal")}
SPARE = [("circle","#5cb85c"),("squircle","#e07ad8"),("drop","#6aa0c8"),("hex","#c48a5a")]
CHAIR_NAMES={"議長","議"}
def F(px): return ImageFont.truetype(FONT, int(px), index=0)
def resolve(weights):
    out=[]; i=0; tot=sum(float(v) for v in weights.values() if float(v)>0) or 1
    weights={n:v for n,v in weights.items() if n not in CHAIR_NAMES}
    tot=sum(float(v) for v in weights.values() if float(v)>0) or 1
    for n,v in weights.items():
        if float(v)<=0: continue
        if n in LOOK: ch,shape,col,eye=LOOK[n]
        else: shape,col=SPARE[i%len(SPARE)]; ch=n[0]; eye="normal"; i+=1
        out.append(dict(name=n,ch=ch,shape=shape,col=col,eye=eye,p=float(v)/tot))
    return sorted(out,key=lambda c:-c["p"])

def body_mask(T,R,shape):
    c=T/2; m=Image.new("L",(T,T),0); d=ImageDraw.Draw(m)
    if shape=="circle": d.ellipse([c-R,c-R,c+R,c+R],fill=255)
    elif shape=="pill": d.rounded_rectangle([c-1.2*R,c-0.75*R,c+1.2*R,c+0.75*R],radius=0.7*R,fill=255)
    elif shape=="squircle": d.rounded_rectangle([c-R,c-R,c+R,c+R],radius=0.45*R,fill=255)
    elif shape=="hex":
        d.polygon([(c+R*math.cos(math.radians(60*i)),c+R*math.sin(math.radians(60*i))) for i in range(6)],fill=255)
        m=m.filter(ImageFilter.GaussianBlur(0.14*R)).point(lambda v:255 if v>120 else 0)
    elif shape=="drop":
        d.ellipse([c-R,c-0.8*R,c+R,c+1.2*R],fill=255)
        d.polygon([(c-0.98*R,c+0.15*R),(c-0.45*R,c-1.2*R),(c+0.7*R,c-0.55*R)],fill=255)
        m=m.filter(ImageFilter.GaussianBlur(0.2*R)).point(lambda v:255 if v>120 else 0)
    return m
def eyes(im, c, R, style):
    d=ImageDraw.Draw(im); w=max(2,int(0.11*R)); ey=c-0.3*R; xs=(c+0.02*R, c+0.42*R)
    def bar(ex,ey,h,ang):
        e=Image.new("RGBA",im.size,(255,255,255,0)); ImageDraw.Draw(e).rounded_rectangle([ex-0.065*R,ey-h/2,ex+0.065*R,ey+h/2],radius=0.065*R,fill="white")
        return e.rotate(ang,center=(ex,ey),resample=Image.BICUBIC)
    if style in ("normal",):
        for ex in xs: im.alpha_composite(bar(ex,ey,0.36*R,18))
    elif style=="big":
        for ex in xs: d.ellipse([ex-0.13*R,ey-0.22*R,ex+0.13*R,ey+0.22*R],fill="white"); d.ellipse([ex-0.05*R,ey-0.05*R,ex+0.07*R,ey+0.12*R],fill="#333")
    elif style=="worry":
        for ex,a in zip(xs,(-35,35)): im.alpha_composite(bar(ex,ey+0.05*R,0.3*R,a))
        d.ellipse([c+0.7*R,c-0.75*R,c+0.86*R,c-0.5*R],fill="#bfe3ff")  # 汗
    elif style=="flat":
        for ex in xs: d.line([(ex-0.12*R,ey),(ex+0.12*R,ey)],fill="white",width=w)
    elif style=="happy":
        for ex in xs: d.arc([ex-0.13*R,ey-0.12*R,ex+0.13*R,ey+0.14*R],200,340,fill="white",width=w)
    elif style=="sleepy":
        for ex in xs: d.arc([ex-0.13*R,ey-0.16*R,ex+0.13*R,ey+0.06*R],20,160,fill="white",width=w)
    elif style=="angry":
        for ex,a in zip(xs,(40,-40)): im.alpha_composite(bar(ex,ey,0.3*R,a))
    elif style=="wink":
        im.alpha_composite(bar(xs[0],ey,0.36*R,18)); d.arc([xs[1]-0.13*R,ey-0.12*R,xs[1]+0.13*R,ey+0.14*R],200,340,fill="white",width=w)
CHAR_IMAGES = {}   # キャラ名 -> 画像パス（JSONの "char_images" か chars/ フォルダから）
def mochi(r, col):
    """絵のないキャラ用：白いもちもちの体（遠藤さんの絵柄に寄せた代わりのキャラ）"""
    k=3; R=r*k; T=int(3.2*R); c=T/2; im=Image.new("RGBA",(T,T),(255,255,255,0)); d=ImageDraw.Draw(im)
    ol="#4a3b3b"; w=max(2,int(0.07*R))
    for sx in (-1,1):  # 足と手
        d.ellipse([c+sx*0.45*R-0.22*R,c+0.78*R,c+sx*0.45*R+0.22*R,c+1.08*R],fill="white",outline=ol,width=w)
        d.ellipse([c+sx*0.9*R-0.2*R,c+0.2*R,c+sx*0.9*R+0.2*R,c+0.55*R],fill="white",outline=ol,width=w)
    d.ellipse([c-R,c-0.95*R,c+R,c+0.95*R],fill="white",outline=ol,width=w)
    for sx in (-1,1):
        d.ellipse([c+sx*0.32*R-0.07*R,c-0.2*R,c+sx*0.32*R+0.07*R,c-0.02*R],fill=ol)
        d.ellipse([c+sx*0.6*R-0.16*R,c+0.02*R,c+sx*0.6*R+0.16*R,c+0.16*R],fill="#ffb8c4")
    d.arc([c-0.12*R,c-0.05*R,c+0.12*R,c+0.15*R],20,160,fill=ol,width=w)
    # 頭の上にキャラ色の星（名前の札は別に付く）
    import math as _m
    pts=[(c+0.22*R*_m.cos(_m.pi/2*3+i*_m.pi/5)*(1 if i%2==0 else 0.45), c-1.12*R+0.22*R*_m.sin(_m.pi/2*3+i*_m.pi/5)*(1 if i%2==0 else 0.45)) for i in range(10)]
    d.polygon(pts,fill=col)
    return im.resize((T//k,T//k),Image.LANCZOS)
def bot(r, c, rot=0):
    if CHAR_IMAGES and c["name"] not in CHAR_IMAGES:
        return mochi(r, c["col"]).rotate(rot*0.5, resample=Image.BICUBIC)
    path = CHAR_IMAGES.get(c["name"])
    if path and os.path.exists(path):
        im = Image.open(path).convert("RGBA"); bb = im.getbbox()
        if bb: im = im.crop(bb)
        sc = 2.9*r / max(im.width, im.height); im = im.resize((max(1,int(im.width*sc)), max(1,int(im.height*sc))), Image.LANCZOS)
        T = int(3.2*r); t = Image.new("RGBA", (T, T), (0,0,0,0)); t.alpha_composite(im, ((T-im.width)//2, (T-im.height)//2))
        return t.rotate(rot*0.5, resample=Image.BICUBIC)
    k=3; R=r*k; T=int(3.2*R); m=body_mask(T,R,c["shape"])
    rgb=tuple(int(c["col"][i:i+2],16) for i in (1,3,5)); im=Image.new("RGBA",(T,T),rgb+(0,)); im.putalpha(m)
    eyes(im,T/2,R,c["eye"]); im=im.rotate(rot,resample=Image.BICUBIC)
    return im.resize((T//k,T//k),Image.LANCZOS)
def tag(cv, x, y, text, col, size, solid=False):
    d=ImageDraw.Draw(cv); f=F(size); w=d.textlength(text,font=f)
    d.rounded_rectangle([x-w/2-0.45*size,y-0.62*size,x+w/2+0.45*size,y+0.62*size],radius=0.62*size,fill=col if solid else "white",outline=col,width=max(2,int(size*0.1)))
    d.text((x,y),text,font=f,fill="white" if solid else col,anchor="mm")

# 横顔と脳（brainmaker と同じ形）
HEAD=[(286,112),(434,120),(517,188),(544,288),(530,389),(485,460),(448,510),(452,611),(267,611),(267,561),(212,544),(165,520),(134,497),(104,493),(89,477),(100,456),(82,443),(93,419),(64,403),(41,386),(60,359),(75,325),(82,272),(110,191),(184,130)]
def smooth(pts,s,n=12):
    out=[]; L=len(pts)
    for i in range(L):
        p0,p1,p2,p3=pts[i-1],pts[i],pts[(i+1)%L],pts[(i+2)%L]
        for t in [j/n for j in range(n)]:
            t2,t3=t*t,t*t*t
            out.append(tuple(0.5*((2*p1[k])+(-p0[k]+p2[k])*t+(2*p0[k]-5*p1[k]+4*p2[k]-p3[k])*t2+(-p0[k]+3*p1[k]-3*p2[k]+p3[k])*t3)*s for k in (0,1)))
    return out
def brain_mask(size,s):
    m=Image.new("L",size,0); d=ImageDraw.Draw(m); cx,cy,rx,ry=318*s,300*s,200*s,140*s
    d.ellipse([cx-rx,cy-ry,cx+rx,cy+ry],fill=255)
    for i in range(22):
        a=-math.pi+i*(2*math.pi/22); r=30*s; x,y=cx+(rx-12*s)*math.cos(a),cy+(ry-12*s)*math.sin(a)
        if y>cy+ry*0.55: continue
        d.ellipse([x-r,y-r,x+r,y+r],fill=255)
    return m.filter(ImageFilter.GaussianBlur(1.5*s)).point(lambda v:255 if v>128 else 0)

def head_panel(state, rnd, s=K):
    """頭1つ分（600x680 の座標系を s 倍）を描く。state = {"weights":{...}, "quote":{"name":..,"text":..}}"""
    size=(600*s,680*s); cv=Image.new("RGBA",size,(0,0,0,0)); d=ImageDraw.Draw(cv)
    hp=smooth(HEAD,s); d.polygon(hp,fill="#f6c59a"); d.line(hp+[hp[0]],fill="#c98a5a",width=3*s,joint="curve")
    mask=brain_mask(size,s); bx=mask.getbbox()
    L=Image.new("RGBA",size,"#f7d3dd"); ld=ImageDraw.Draw(L)
    for _ in range(70):
        x,y=rnd.randint(bx[0],bx[2]),rnd.randint(bx[1],bx[3]); rr=rnd.randint(10,24)*s
        ld.arc([x-rr,y-rr,x+rr,y+rr],rnd.randint(0,180),rnd.randint(200,360),fill="#efbccb",width=2*s)
    cs=resolve(state["weights"]); cx=(bx[0]+bx[2])/2; cy=(bx[1]+bx[3])/2+28*s; tw,th=74*s,24*s
    ld.ellipse([cx-tw,cy-th+9*s,cx+tw,cy+th+9*s],fill="#a9745a"); ld.ellipse([cx-tw,cy-th,cx+tw,cy+th],fill="#c98f6e")
    n=len(cs); seats=[]
    # 一番大きいキャラは手前中央、残りは奥側に左右交互
    SEATS=[math.pi/2, -0.95, -math.pi+0.95, -math.pi/2, 0.7, math.pi-0.7, -0.35, -math.pi+0.35]
    angs=SEATS[:n]+[rnd.uniform(-3,0) for _ in range(max(0,n-len(SEATS)))]
    for c,a in zip(cs,angs):
        r=(16+78*c["p"])*s  # 割合にほぼ比例（差がはっきり出る）
        x=cx+(tw+14*s+0.55*r)*math.cos(a); y=cy+(th+26*s)*math.sin(a)-4*s
        if a==math.pi/2: y=min(cy+th*0.4+r*0.6, bx[3]-r*1.35-22*s)
        c["xy"]=[x,y,r]
    # 重なりをほどく（押し合い）。脳の外に出ないように枠内へ戻す
    you_seated=state.get("you_seated", False)
    fixed=[dict(name="議長",ch="議",shape="hex",col="#6cb85c",eye="normal",p=0,xy=[cx+tw+22*s,cy-4*s,17*s],chair=True)]
    for _ in range(120):
        allc=cs+fixed
        for i,a in enumerate(allc):
            for b in allc[i+1:]:
                dx=b["xy"][0]-a["xy"][0]; dy=b["xy"][1]-a["xy"][1]; dist=math.hypot(dx,dy) or 1
                need=(a["xy"][2]+b["xy"][2])*1.1+26*s
                if dist<need:
                    ux,uy=dx/dist,dy/dist; fa="name" in a and (a.get("chair") or a.get("you")); fb=(b.get("chair") or b.get("you"))
                    m=(need-dist)/(1 if (fa or fb) else 2)
                    if not fa: a["xy"][0]-=ux*m; a["xy"][1]-=uy*m*0.9
                    if not fb: b["xy"][0]+=ux*m; b["xy"][1]+=uy*m*0.9
        for c in cs:
            x,y,r=c["xy"]
            c["xy"][0]=min(max(x,bx[0]+r+24*s),bx[2]-r-24*s)
            c["xy"][1]=min(max(y,bx[1]+r+30*s),bx[3]-r-34*s)
    for c in sorted(cs+fixed,key=lambda c:c["xy"][1]):
        x,y,r=c["xy"]
        t=bot(r,c,rot=rnd.uniform(-10,10)); ox,oy=int(x-t.width/2),int(y-t.height/2); L.alpha_composite(t,(ox,oy))
        ab=t.getbbox() or (0,0,t.width,t.height); c["body"]=(ox+ab[0],oy+ab[1],ox+ab[2],oy+ab[3])
        am=Image.new("L",size,0); am.paste(t.getchannel("A").point(lambda v:255 if v>140 else 0),(ox,oy)); c["alpha"]=am
    cv.paste(L,(0,0),mask)
    edge=mask.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(5)); cv.paste(Image.new("RGBA",size,"#6d4c41"),(0,0),edge)
    # 吹き出し（1つだけ）：先に位置だけ決める（札をよけるため）
    q=state.get("quote"); bub=None; avoid=[]
    if q:
        tgt=next((c for c in cs if c["name"]==q["name"]), cs[0]); x,y,r=tgt["xy"]; bx=mask.getbbox()
        f=F(19*s); text=q["text"]; lines=[]; cur=""
        for ch in text:
            if d.textlength(cur+ch,font=f)>300*s: lines.append(cur); cur=ch
            else: cur+=ch
        lines.append(cur); lh=26*s; bw=max(d.textlength(l,font=f) for l in lines)+30*s; bh=lh*len(lines)+20*s
        bx0=max(40*s,min(size[0]-bw-40*s, x-bw/2)); by0=bx[1]-bh+18*s
        bub=(tgt,x,y,r,f,lines,lh,bw,bh,bx0,by0)
        avoid.append((bx0-4*s,by0-20*s,bx0+bw+4*s,by0+bh+4*s))                 # 吹き出し
        avoid.append((x-14*s,by0+bh,x+14*s,y-r*0.9))                            # 吹き出しのしっぽ
    # 名前の札：ぶつからない場所を探して、最後に描く（札どうし・ほかのキャラの体・吹き出し・脳の外を避ける）
    place_tags(cv, d, cs, fixed, avoid, mask, s)
    if bub:
        tgt,x,y,r,f,lines,lh,bw,bh,bx0,by0=bub; dd=ImageDraw.Draw(cv)
        dd.polygon([(x-12*s,by0+bh-2*s),(x+12*s,by0+bh-2*s),(x,y-r*0.9)],fill=tgt["col"])
        dd.rounded_rectangle([bx0,by0,bx0+bw,by0+bh],radius=16*s,fill="white",outline=tgt["col"],width=6*s)
        for i,l in enumerate(lines): dd.text((bx0+15*s,by0+10*s+i*lh),l,font=f,fill="#333")
        tag(cv,bx0+20*s+d.textlength(tgt["name"],font=F(20*s))/2,by0-4*s,tgt["name"]+"の声",tgt["col"],20*s,solid=True)
    for t in PLACED[-1]["tags"]: tag(cv,t["x"],t["y"],t["text"],t["col"],t["sz"])
    return cv

PLACED=[]   # 確認用：パネルごとの札・体・よける範囲
def _ov(a,b):
    w=min(a[2],b[2])-max(a[0],b[0]); h=min(a[3],b[3])-max(a[1],b[1])
    return w*h if w>0 and h>0 else 0
def _px(img, rc):
    """rc の中で img が塗られているピクセル数"""
    W,H=img.size; x0,y0,x1,y1=max(0,int(rc[0])),max(0,int(rc[1])),min(W,int(rc[2])),min(H,int(rc[3]))
    if x1<=x0 or y1<=y0: return 0
    return img.crop((x0,y0,x1,y1)).histogram()[255]
def place_tags(cv, d, cs, fixed, avoid, mask, s):
    from PIL import ImageChops
    W,H=mask.size
    def inside(rc):
        for px,py in ((rc[0],rc[1]),(rc[2],rc[1]),(rc[0],rc[3]),(rc[2],rc[3]),((rc[0]+rc[2])/2,rc[1]),((rc[0]+rc[2])/2,rc[3])):
            px=int(min(max(px,0),W-1)); py=int(min(max(py,0),H-1))
            if mask.getpixel((px,py))<128: return False
        return True
    allc=[c for c in cs+fixed if "alpha" in c]
    others={}
    for c in cs:
        o=Image.new("L",(W,H),0)
        for e in allc:
            if e is not c: o=ImageChops.lighter(o,e["alpha"])
        others[c["name"]]=o
    placed=[]
    for c in sorted(cs,key=lambda c:-c["xy"][2]):      # 大きいキャラから
        x,y,r=c["xy"]; sz=max(11*s,min(17*s,0.32*r+7*s)); text=f"{c['name']} {round(c['p']*100)}%"
        w=d.textlength(text,font=F(sz))+0.9*sz+2*s; h=1.24*sz+2*s; b0=c["body"]
        cands=[(x,y+r*1.02+8*s),(x,b0[3]+h/2),(x,b0[1]-h/2),(b0[2]+w/2,(b0[1]+b0[3])/2),(b0[0]-w/2,(b0[1]+b0[3])/2)]
        for dy in (0,0.25,0.5,0.75,1.0,1.5,2.0,2.5,3.0,-0.25,-0.5,-0.75,-1.0,-1.5,-2.0,-2.5,-3.0,-3.5,-4.0,-5.0):
            for dx in (0,-0.15,0.15,-0.3,0.3,-0.45,0.45,-0.6,0.6,-0.9,0.9,-1.2,1.2,-1.6,1.6,-2.0,2.0):
                cands.append((x+dx*w,y+r*1.02+8*s+dy*h))
        x0d,y0d=cands[0]; cands=cands[:3]+sorted(cands[3:],key=lambda q:math.hypot(q[0]-x0d,(q[1]-y0d)*1.6))   # 近い場所から
        best=None; oth=others[c["name"]]
        for i,(tx,ty) in enumerate(cands):
            rc=(tx-w/2,ty-h/2,tx+w/2,ty+h/2)
            cost=0 if inside(rc) else 1e12
            cost+=sum(_ov(rc,p["rect"]) for p in placed)*100
            cost+=_px(oth,rc)*100
            cost+=sum(_ov(rc,a) for a in avoid)*100
            cost+=i*1e-3
            if best is None or cost<best[0]: best=(cost,tx,ty,rc)
            if cost<1: break
        _,tx,ty,rc=best
        placed.append(dict(name=c["name"],x=tx,y=ty,text=text,col=c["col"],sz=sz,rect=rc))
    PLACED.append(dict(tags=placed,others=others,avoid=avoid))

def wrap(d, text, f, maxw):
    lines=[]; cur=""
    for ch in text:
        if d.textlength(cur+ch,font=f)>maxw: lines.append(cur); cur=ch
        else: cur+=ch
    return lines+[cur]
NO_HEAD="、。，．！？!?」』）)ー…・ぁぃぅぇぉっゃゅょ"   # 行の頭に来てはいけない文字
BREAK_AFTER="、。，．！？!?　 "                         # ここで切ると自然
PARTICLES="はがをにでともかへやの"                       # 助詞のあとも自然
def worry_lines(d, worry, maxw, big=30*K, small1=24*K, small2=20*K):
    """悩みを「」付きで1行に収める。入らなければ文字を小さくし、それでも無理なら
    自然な切れ目で2行に分ける（1文字や」だけが次の行に落ちないようにする）。"""
    text="「"+worry.strip()+"」"
    for fs in range(big, small1-1, -K):
        if d.textlength(text,font=F(fs))<=maxw: return fs,[text]
    n=len(text); best=None
    for fs in range(big, small2-1, -K):
        f=F(fs)
        for i in range(3, n-2):                     # 各行に3文字以上
            a,b=text[:i],text[i:]
            if b[0] in NO_HEAD or a[-1]=="「": continue
            wa,wb=d.textlength(a,font=f),d.textlength(b,font=f)
            if max(wa,wb)>maxw: continue
            nat=0 if a[-1] in BREAK_AFTER else (0.08 if a[-1] in PARTICLES and not b[0] in PARTICLES else 0.35)
            cost=abs(wa-wb)/maxw+nat
            if best is None or cost<best[0]: best=(cost,[a,b])
        if best: return fs,best[1]
    f=F(small2); return small2,wrap(d,text,f,maxw)[:2]
def make(data, out, seed=None, base="."):
    CHAR_IMAGES.clear()
    # スクリプトの隣の chars/ を先に読み、JSONと同じ場所に chars/ があれば上書き
    here = os.path.dirname(os.path.abspath(__file__))
    for cdir in dict.fromkeys([os.path.join(here, "chars"), os.path.join(os.path.abspath(base), "chars")]):
        if not os.path.isdir(cdir): continue
        for f in os.listdir(cdir):
            n, e = os.path.splitext(f)
            if e.lower() in (".png", ".webp", ".jpg", ".jpeg"): CHAR_IMAGES[n] = os.path.join(cdir, f)
    for n, pth in (data.get("char_images") or {}).items():
        CHAR_IMAGES[n] = pth if os.path.isabs(pth) else os.path.join(base, pth)
    rnd=random.Random(seed); cv=Image.new("RGBA",(CW,CH),"#fff8e7"); d=ImageDraw.Draw(cv)
    d.rectangle([0,0,CW-1,CH-1],outline="#f4a6b8",width=8*K)
    # 上：悩み
    d.text((28*K,22*K),"脳内メーカー",font=F(18*K),fill="#e64980")
    # 左上の「脳内メーカー」の幅を左右に空けて、その間に悩みを置く（重ならない）
    side=28*K+d.textlength("脳内メーカー",font=F(18*K))+18*K
    fs,wl=worry_lines(d,data["worry"],CW-2*side)
    lh=fs*1.22; y0=48*K-(len(wl)-1)*lh*0.3
    for i,l in enumerate(wl): d.text((CW/2,y0+i*lh),l,font=F(fs),fill="#333",anchor="mm")
    # 中：前と後（悩みの行の下から）
    top=int(y0+(len(wl)-1)*lh+fs/2+21*K); crop=(30,40,575,615)
    for j,(key,label) in enumerate((("before","会議の前"),("after","会議の後"))):
        p=head_panel(data[key],rnd).crop(tuple(v*K for v in crop))
        sc=(CH-top-118*K)/p.height; p=p.resize((int(p.width*sc),int(p.height*sc)),Image.LANCZOS)
        x0=int((70 if j==0 else 640)*K + (500*K-p.width)/2); cv.alpha_composite(p,(x0,top+6*K))
        tag(cv,x0+60*K,int(top+(CH-top-118*K)*0.93),label,"#e64980" if j else "#888",17*K)
    ay=top+(CH-top-118*K)/2; d.polygon([(585*K,ay-28*K),(625*K,ay),(585*K,ay+28*K)],fill="#e64980")
    d.text((605*K,ay+46*K),"話し合い",font=F(14*K),fill="#e64980",anchor="mm")
    # 「その後の様子」画像（任意）を後の頭の右下に小さく
    img=data.get("image")
    if img and os.path.exists(img):
        pic=Image.open(img).convert("RGB"); R=92*K; s=max(2*R/pic.width,2*R/pic.height)
        pic=pic.resize((int(pic.width*s)+1,int(pic.height*s)+1),Image.LANCZOS); pic=pic.crop(((pic.width-2*R)//2,(pic.height-2*R)//2,(pic.width-2*R)//2+2*R,(pic.height-2*R)//2+2*R))
        bx,by=1088*K,CH-215*K; cm=Image.new("L",(2*R,2*R),0); ImageDraw.Draw(cm).ellipse([0,0,2*R,2*R],fill=255)
        d.ellipse([bx-R-5*K,by-R-5*K,bx+R+5*K,by+R+5*K],fill="white",outline="#6d4c41",width=3*K); cv.paste(pic,(bx-R,by-R),cm)
        tag(cv,bx,by+R+4*K,"その後の様子","#6d4c41",15*K)
    # 下：結論
    d.rounded_rectangle([40*K,CH-104*K,CW-40*K,CH-24*K],radius=20*K,fill="#e8708f")
    f=F(24*K); wl=wrap(d,data.get("conclusion_label","あなたの選択")+"："+data["conclusion"],f,1060*K)[:2]
    for i,l in enumerate(wl): d.text((CW/2,CH-64*K+(i-(len(wl)-1)/2)*30*K),l,font=f,fill="white",anchor="mm")
    cv.convert("RGB").resize((CW//K,CH//K),Image.LANCZOS).save(out); return out
if __name__=="__main__":
    data=json.load(open(sys.argv[1],encoding="utf-8")); base=os.path.dirname(os.path.abspath(sys.argv[1]))
    if data.get("image") and not os.path.isabs(data["image"]): data["image"]=os.path.join(base,data["image"])
    if data.get("image") and not os.path.exists(data["image"]): print("注意: image が見つからないので画像なしで作ります:", data["image"], file=sys.stderr)
    print(make(data, sys.argv[2] if len(sys.argv)>2 else "card.png", int(sys.argv[3]) if len(sys.argv)>3 else 1, base=base))
