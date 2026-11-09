typedef unsigned long long U; typedef unsigned int W; typedef unsigned char B;
__attribute__((section(".telemetry"))) volatile U hud_debug[32];
static B pool[0x50000] __attribute__((aligned(16))); static W used;
static const char stamina[]="Pa_StaminaGauge_00";
static int eq(const char*a,const char*b){if(!a||!b)return 0;for(W i=0;i<96;i++){if(a[i]!=b[i])return 0;if(!a[i])return 1;}return 0;}
static void cp(void*d,const void*s,W n){for(W i=0;i<n;i++)((B*)d)[i]=((const B*)s)[i];}
static U q(const void*p,W o){return *(const U*)((const B*)p+o);} static W w(const void*p,W o){return *(const W*)((const B*)p+o);}
static void *alloc(W n){n=(n+15)&~15u;if(n>sizeof(pool)-used){hud_debug[15]++;return 0;}void*p=pool+used;used+=n;hud_debug[14]=used;return p;}
static void *clone(const void*s,W n){void*p=alloc(n);if(p)cp(p,s,n);return p;}
static int indexof(B*r,W table,const char*name){W n=w(r,table+24);if(n>512)return -1;U *names=(U*)q(r,table);for(W i=0;i<n;i++)if(eq((char*)names[i],name))return i;return -1;}
/* Arrays and descriptors are copied privately; the shared resource remains read-only. */
static B* rootclone(B*r){
 int ci=indexof(r,0x20,"Pa_MpGauge_00"),pi=indexof(r,0xc0,"Pa_MpGauge_00");
 if(ci<0||pi<0||indexof(r,0x20,stamina)>=0)return 0;
 W nc=w(r,0x38),np=w(r,0xd8);if(nc>128||np>128)return 0;
 B*out=clone(r,0x228); B*common=clone((void*)((U*)q(r,0x28))[ci],68); B*part=clone((void*)((U*)q(r,0xc8))[pi],88); B*first=clone((void*)((U*)q(r,0x28))[0],68);
 if(!out||!common||!part||!first)return 0;
 *(W*)(common+40)=0;*(W*)(common+52)=nc+1;*(W*)(common+64)=0x7ffff;common[56]|=1;
 /* Full-width, half-height gauge with clearance below magic. */
 *(float*)(common+16)=1;*(float*)(common+20)=.5f;
 *(float*)(common+28)=-1560;*(float*)(common+32)=736;
 *(W*)(first+52)=nc+1;*(W*)(part+64)=nc;
 for(W t=0;t<2;t++){
  W off=t?0xc0:0x20,n=t?np:nc;
  for(W j=0;j<3;j++){
   U*a=alloc((n+1)*8);if(!a)return 0;cp(a,(void*)q(r,off+j*8),n*8);
   a[n]=j==0?(U)stamina:j==1?(U)(t?part:common):STAMINA_HASH;
   if(!t&&j==1)a[0]=(U)first;
   *(U*)(out+off+j*8)=(U)a;
  }
  *(W*)(out+off+24)=n+1;
 }
 hud_debug[3]++;return out;
}
static B*gaugeclone(B*r){
 B*base=r-0xf8;W n=w(base,8);if(w(base,0)!=0x48464642||n<0x7500||n>0x10000)return 0;
 B*out=clone(base,n);if(!out)return 0;
 for(W i=0;i+8<=n;i+=8){U v=q(out,i);if(v>=(U)base&&v<(U)base+n)*(U*)(out+i)=(U)out+v-(U)base;}
 /* Only this private fill uses the stock white texture. */
 for(W i=0;i+8<=n;i+=8){U v=q(out,i);if(v>=(U)out&&v<(U)out+n&&eq((char*)v,"MpGaugeCenter_00")){*(U*)(out+i)=(U)"White8_00_BC4L";hud_debug[6]++;}}
 float*white=(float*)(out+0x74d8);if(white[0]==1&&white[1]==1&&white[2]==1&&white[3]==1){white[1]=.85f;white[2]=.15f;}
 float*c=(float*)(out+0x74e8);if(c[1]>.5646f&&c[1]<.5648f){c[0]=1;c[1]=.85f;c[2]=.15f;c[3]=1;hud_debug[7]++;}
 *(U*)(out+0x110)=(U)"PaStaminaGauge_00";hud_debug[4]++;return out+0xf8;
}
static B* wheelclone(B*r,W kind){
 W n=w(r,0x38);if(n>512)return 0;B*out=clone(r,0x228);U*descs=clone((void*)q(r,0x28),n*8);if(!out||!descs)return 0;*(U*)(out+0x28)=(U)descs;
 for(W i=0;i<n;i++){
  const char*name=(char*)((U*)q(r,0x20))[i];
  W resize=kind==3&&(eq(name,"N_SlideList_00")||eq(name,"S_ScissorHT_00"));
  W text=kind==3&&eq(name,"T_Text_00");
  W hide=kind==3?(eq(name,"N_Cursor_00")||eq(name,"N_Arrow_00")||eq(name,"N_Arrow_01")||eq(name,"P_CursorSh_00")||eq(name,"Pa_ShortCutScrollBar_00")):(eq(name,"P_MaskR_00")||eq(name,"P_MaskL_00")||eq(name,"C_CaptureR_00")||eq(name,"C_CaptureL_00")||eq(name,"Pa_SortWindow_00")||eq(name,"A_Guide_00")||eq(name,"A_Guide_01"));
  if(!resize&&!text&&!hide)continue;
  B*d=clone((void*)descs[i],68);if(!d)return 0;descs[i]=(U)d;
  if(resize||text){*(float*)(d+32)=0;if(resize){*(float*)(d+44)=24000;*(float*)(d+48)=2160;}}
  if(hide){*(float*)(d+16)=0;*(float*)(d+20)=0;}
 }
 hud_debug[8]++;return out;
}
/* Resource variants are cached independently, including each HUD skin's input. */
static struct{B*source,*copy;W kind;}resources[24];static W resource_count;
static struct{void*handle;B config[0x100];}calls[64];static W call_count;
void*hud_prepare(void*handle,B*config){
 hud_debug[0]++; B*r=(B*)q(config,0);if(!r||w(r,0)!=0x004c4955)return config;
 const char*asset=(char*)q(r,0x18),*instance=(char*)q(handle,0x30);hud_debug[1]=(U)asset;hud_debug[2]=(U)instance;
 W kind=eq(asset,"PlayerStatus_00")?1:eq(instance,stamina)?2:eq(asset,"PaShortCutSlideList_00")?3:eq(asset,"ShortCut_01")?4:0;if(!kind)return config;
 hud_debug[16]=(U)r;hud_debug[17]=(U)handle;hud_debug[18]=(U)config; B*replacement=0;W i;for(i=0;i<resource_count;i++)if(resources[i].source==r&&resources[i].kind==kind){replacement=resources[i].copy;break;}
 if(i==resource_count){if(resource_count==24)return config;replacement=kind==1?rootclone(r):kind==2?gaugeclone(r):wheelclone(r,kind);if(!replacement)return config;resources[i].source=r;resources[i].copy=replacement;resources[i].kind=kind;resource_count++;}
 for(i=0;i<call_count;i++)if(calls[i].handle==handle)break;
 if(i==call_count){if(call_count==64)return config;calls[i].handle=handle;call_count++;}
 cp(calls[i].config,config,0x100);*(U*)calls[i].config=(U)replacement;hud_debug[19]=(U)replacement;hud_debug[5]++;return calls[i].config;
}
U hud_pane(U frame,const char*name){B*layout=(B*)q((void*)frame,0x80);if(!layout)return 0;B*r=(B*)q(layout,0xf8);if(!r)return 0;int i=indexof(r,0x20,name);return i<0?0:q(layout,0x100)+(U)i*0xb0;}
