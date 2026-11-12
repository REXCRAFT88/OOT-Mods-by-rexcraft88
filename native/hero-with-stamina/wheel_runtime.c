#ifdef HERO_UNIFIED
#include "settings.h"
#endif
typedef unsigned long long u64;
typedef unsigned u32;
typedef unsigned char u8;
extern u8 wheel_cache[],pad_global[];
extern void set_index(void*,unsigned,unsigned,unsigned,unsigned);
extern void change_focus(void*,unsigned,unsigned);
extern void equip_index(void*,unsigned);
extern void commit_item(void*,unsigned);
#ifdef HERO_UNIFIED
extern void native_stock_wheel_update(void*);
extern void hud_selector_layout(void*,unsigned);
#endif
static void* ptr(void* p,unsigned off){return *(void**)((u8*)p+off);}
/* Small periodic approximation; no libc or new graphics allocations. */
static float sine(float t){
 while(t>3.14159265f)t-=6.2831853f;
 float x=t<0?-t:t;
 float q=x*(3.14159265f-x);
 float v=16*q/(49.348022f-4*q);
 return t<0?-v:v;
}
static unsigned count(void* list){void* c=ptr(wheel_cache,48);return c?*(u32*)((u8*)c+0x78):0;}
static unsigned key(unsigned i){
 u8* w=ptr(wheel_cache,264+16*i);
 if(!w)return i;
 char* s=(char*)w+0x94;
 if(s[0]=='W'||(s[0]=='P'&&s[6]=='R')||(s[5]=='A'&&s[6]=='r'))return 100;
 if(s[5]=='B'&&s[7]=='t')return 101;
 if((s[5]=='D'&&s[6]=='i')||(s[5]=='F'&&s[6]=='a')||(s[5]=='N'&&s[6]=='a'))return 102;
 if(s[5]=='M'&&s[6]=='a')return 103;
 return i;
}
static unsigned groups(unsigned n){
 unsigned g=0;u8* map=wheel_cache+1536;
 for(unsigned i=0;i<n;i++){
  unsigned j=0,k=key(i);
  while(j<g&&key(map[j])!=k)j++;
  if(j==g)map[g++]=i;
 }
 return g;
}
void wheel_update(void* controller){
#ifdef HERO_UNIFIED
 if(!hero_wheel_enabled()){
  if(ptr(controller,0x68)==ptr(wheel_cache,16))
   *(void**)(wheel_cache+48)=controller;
  native_stock_wheel_update(controller);
  return;
 }
#endif
 void* list=ptr(controller,0x68);
 if(list!=ptr(wheel_cache,16))return;
 *(void**)(wheel_cache+48)=controller;
 void* owner=ptr(controller,0x20);void* screen=ptr(controller,0x18);
 if(!owner||!screen||*((u8*)owner+0x3a)!=2||*((u8*)screen+0x1a6)!=2)return;
 if(*(signed char*)((u8*)screen+0x1a5)<0)return;
 unsigned n=count(list),best=0;
 /* Binding populates the widget cache incrementally. Refuse to draw/select
    until the current list has been completely rebound after a reload. */
 if(!n||n>64||*(u32*)(wheel_cache+36)!=n)return;
 unsigned g=groups(n);u8* map=wheel_cache+1536;
 void* root=*(void**)pad_global;
 if(!root)return;
 void* pad=ptr(root,0xc0);
 if(!pad)return;
 /* Native pad state stores the right stick immediately after the left pair. */
 float x=*(float*)((u8*)pad+0x128),y=*(float*)((u8*)pad+0x12c);
 /* Both sticks contribute equally; opposing directions cancel without a side preference. */
 float lx=*(float*)((u8*)pad+0x120),ly=*(float*)((u8*)pad+0x124);
 if(x*x+y*y<.1225f){x=0;y=0;}
 if(lx*lx+ly*ly>=.1225f){x+=lx;y+=ly;}
 if(x*x+y*y<.1225f)return;
 float score=-1e10f;
 for(unsigned i=0;i<g;i++){
  float a=6.2831853f*i/g;
  float d=x*sine(a)+y*sine(a+1.5707963f);
  if(d>score){score=d;best=i;}
 }
 best=map[best];
 unsigned old=*(u32*)((u8*)list+0x4c);
 if(best==old)return;
 /* Native focus, label and equipped-item routines retain item semantics. */
 set_index(list,best,0,0,1);
 change_focus(controller,old,best);
 equip_index(controller,best);
}
void wheel_draw(void* list){
#ifdef HERO_UNIFIED
 if(list==ptr(wheel_cache,16)){
  void* frame=ptr(list,0x20);
  if(frame)hud_selector_layout(frame,hero_wheel_enabled());
 }
 if(!hero_wheel_enabled())return;
#endif
 if(list!=ptr(wheel_cache,16))return;
 unsigned n=count(list);
 if(!n||n>64||*(u32*)(wheel_cache+36)!=n)return;
 unsigned g=groups(n);u8* map=wheel_cache+1536;
 float radius=280+40*g;
 if(radius>800)radius=800;
 unsigned selected=*(u32*)((u8*)list+0x4c),focus=0;
 for(unsigned i=0;i<g;i++)if(key(map[i])==key(selected))focus=i;
 /* Reuse the stock animated white cursor line and glow, now on the ring. */
 void* frame=ptr(list,0x20);
 void* layout=frame?ptr(frame,0x80):0;
 u8* cursor=layout?ptr(layout,0x100):0;
 if(cursor){
  cursor+=0xb0;
  float a=6.2831853f*focus/g;
  *(float*)(cursor+0x6c)=radius*sine(a);
  *(float*)(cursor+0x70)=radius*sine(a+1.5707963f);
  *(float*)(cursor+0x60)=.85f;*(float*)(cursor+0x64)=.85f;
  *(u32*)cursor|=0x6f;
 }
 for(unsigned i=0;i<n;i++){
  void* widget=ptr(wheel_cache,264+16*i);
  if(!widget)continue;
  void* frame=ptr(widget,0x20);
  if(!frame)continue;
  void* layout=ptr(frame,0x80);
  if(!layout)continue;
  u8* pane=ptr(layout,0x100);
  if(!pane)continue;
  unsigned slot=0;
  while(slot<g&&map[slot]!=i)slot++;
  float a=6.2831853f*slot/g;
  *(float*)(pane+0x6c)=radius*sine(a);
  *(float*)(pane+0x70)=radius*sine(a+1.5707963f);
  float s=key(i)==key(*(u32*)((u8*)list+0x4c))?.88f:.70f;
  if(slot==g)s=0;
  *(float*)(pane+0x60)=s;*(float*)(pane+0x64)=s;
  *(u32*)pane|=0x6f;
 }
}
extern void hero_guard_frame(void);
void wheel_tick(void){
 hero_guard_frame();
#ifdef HERO_UNIFIED
 if(!hero_wheel_enabled()){*(u32*)(wheel_cache+112)=0;return;}
#endif
 if(*(u32*)(wheel_cache+112)){
  unsigned event=*(u32*)(wheel_cache+112);
  *(u32*)(wheel_cache+112)=0;
  void* c=ptr(wheel_cache,48);void* list=ptr(wheel_cache,16);
  if(c&&list){
   unsigned n=count(list),selected=*(u32*)((u8*)list+0x4c),old=selected,next=selected;
   if(!n||n>64||selected>=n||*(u32*)(wheel_cache+36)!=n)return;
   if(event==2){*(u32*)(wheel_cache+116)=old+1;return;}
   unsigned remembered=*(u32*)(wheel_cache+116);
   if(remembered&&remembered<=n&&key(remembered-1)==key(old))old=remembered-1;
   if(n&&n<=64)for(unsigned j=1;j<n;j++){
    unsigned i=(old+j)%n;
    if(key(i)==key(old)){next=i;break;}
   }
   *(u32*)(wheel_cache+116)=next+1;
   if(next!=old){set_index(list,next,0,0,1);change_focus(c,selected,next);equip_index(c,next);commit_item(c,0);}
  }
 }
}
void wheel_raw(u64* state,unsigned count){
 u64 sample=state[0];u32 held=(state[1]&128)!=0;
 u32* last=(u32*)(wheel_cache+68);
 if(held&&!*last)*(u64*)(wheel_cache+96)=sample;
 if(!held&&*last)
  *(u32*)(wheel_cache+112)=sample-*(u64*)(wheel_cache+96)<=192?1:2;
 *last=held;
 /* Keep a tap out of the native menu input; forward only a sustained hold. */
 if(held&&sample-*(u64*)(wheel_cache+96)<=192)
  for(unsigned i=0;i<count;i++)state[i*5+1]&=~128ull;
}
