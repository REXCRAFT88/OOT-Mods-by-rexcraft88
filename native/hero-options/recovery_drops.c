#include "settings.h"
typedef unsigned u32;
typedef unsigned long long u64;
extern u32 native_name_hash(const char *,u32);

static int same(const char *a,const char *b) {
    if (!a || !b) return 0;
    for (u32 i=0;i<128;i++) {
        if (a[i]!=b[i]) return 0;
        if (!a[i]) return 1;
    }
    return 0;
}
static int recovery(const char *name) {
    return same(name,"Obj_Heart") || same(name,"Obj_MagicJar_Small") ||
           same(name,"Obj_MagicJar_Large") || same(name,"Obj_Fairy");
}

/* Native DropLottery output: FixedObjArray<name/hash record>, count/capacity
   at +0/+4 and record-pointer array at +8. Records retain native ownership.
   Only the borrowed name pointer and cached name hash change. No allocation,
   actor creation, inventory mutation or direct save access occurs here. */
void hero_filter_recovery_drops(void *output) {
    if (!hero_no_recovery_drops() || !output) return;
    u32 *header=output, count=header[0], capacity=header[1];
    if (!count || count>capacity || capacity>64) return;
    u64 *items=*(u64 **)((char *)output+8);
    if (!items) return;
    for (u32 i=0;i<count;i++) {
        unsigned char *record=(unsigned char *)items[i];
        if (!record) continue;
        const char *name=*(const char **)record;
        if (!name) continue;
        const char *replacement=0;
        if (recovery(name)) replacement="Obj_Rupee_Green";
        else if (same(name,"Work/Actor/Obj_Heart.engine__actor__ActorParam.gyml") ||
                 same(name,"Work/Actor/Obj_MagicJar_Small.engine__actor__ActorParam.gyml") ||
                 same(name,"Work/Actor/Obj_MagicJar_Large.engine__actor__ActorParam.gyml") ||
                 same(name,"Work/Actor/Obj_Fairy.engine__actor__ActorParam.gyml"))
            replacement="Work/Actor/Obj_Rupee_Green.engine__actor__ActorParam.gyml";
        if (!replacement) continue;
        *(const char **)record=replacement;
        *(u32 *)(record+8)=native_name_hash(replacement,0);
    }
}
