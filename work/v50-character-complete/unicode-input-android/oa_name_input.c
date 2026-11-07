#include "oa_name_input.h"
#include "oa_creation.h"
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
static int accepted(const char *s){
 oa_creation_state temporary;size_t n;if(!s)return 0;n=strlen(s);if(n>64)return 0;if(!n)return 1;
 return !oa_creation_begin(&temporary,OA_CREATION_ALMAIN,OA_CREATION_MALE)&&!oa_creation_set_name(&temporary,s,n);
}
#ifdef OA_DESKTOP
#include "oa_desktop_name_input.h"
struct oa_name_input{int active;};
oa_name_input *oa_name_input_open(ANativeActivity *a){(void)a;return (oa_name_input*)calloc(1,sizeof(oa_name_input));}
int oa_name_input_available(const oa_name_input *p){return p!=NULL;}
int oa_name_input_show(oa_name_input *p,const char *s){if(!p||!accepted(s))return 0;p->active=oa_desktop_name_input(1,s)>=0;return p->active;}
void oa_name_input_hide(oa_name_input *p){if(p){oa_desktop_name_input(0,"");p->active=0;}}
void oa_name_input_close(oa_name_input *p){if(p){oa_name_input_hide(p);free(p);}}
void oa_name_input_sync(oa_name_input *p,const char *s){if(p&&p->active&&accepted(s))oa_desktop_name_input(1,s);}
int oa_name_input_poll(oa_name_input *p,char *s,size_t n,int *done){return p?oa_desktop_name_poll(s,n,done):0;}
#else
#include <jni.h>
#include <pthread.h>
#include <android/log.h>
struct oa_name_input{
 JavaVM *vm;jobject activity;jclass helper;jmethodID open,sync,hide;
 pthread_mutex_t lock;uint64_t token,delivered;int active,pending,confirmed;
 char value[65],last_sync[65];uint64_t revision;
};
static pthread_mutex_t registry_lock=PTHREAD_MUTEX_INITIALIZER;
static oa_name_input *registry[8];static uint64_t next_token;
static JNIEnv *environment(oa_name_input *p,int *detach){
 JNIEnv *e=NULL;jint result;*detach=0;result=(*p->vm)->GetEnv(p->vm,(void**)&e,JNI_VERSION_1_6);
 if(result==JNI_EDETACHED){if((*p->vm)->AttachCurrentThread(p->vm,&e,NULL)!=JNI_OK)return NULL;*detach=1;}
 else if(result!=JNI_OK)return NULL;return e;
}
static void release_env(oa_name_input *p,int detach){if(detach)(*p->vm)->DetachCurrentThread(p->vm);}
static int exception(JNIEnv *e){if(!(*e)->ExceptionCheck(e))return 0;(*e)->ExceptionClear(e);__android_log_print(ANDROID_LOG_ERROR,"OpemAmalurScene","Name input Java bridge failed");return 1;}
static int from_utf16(JNIEnv *e,jstring s,char out[65]){
 const jchar *p;jsize n;size_t at=0;unsigned count=0;jsize i;
 if(!s)return 0;n=(*e)->GetStringLength(e,s);if(n>32)return 0;
 p=(*e)->GetStringChars(e,s,NULL);if(!p)return 0;
 for(i=0;i<n;i++){
  uint32_t c=p[i];if(c>=0xd800&&c<=0xdbff){if(i+1>=n||p[i+1]<0xdc00||p[i+1]>0xdfff)goto bad;c=0x10000+((c-0xd800)<<10)+(p[++i]-0xdc00);}
  else if(c>=0xdc00&&c<=0xdfff)goto bad;
  if(c<32||c==127||++count>16)goto bad;
  if(c<128)out[at++]=(char)c;
  else if(c<2048){out[at++]=(char)(0xc0|(c>>6));out[at++]=(char)(0x80|(c&63));}
  else if(c<65536){out[at++]=(char)(0xe0|(c>>12));out[at++]=(char)(0x80|((c>>6)&63));out[at++]=(char)(0x80|(c&63));}
  else{out[at++]=(char)(0xf0|(c>>18));out[at++]=(char)(0x80|((c>>12)&63));out[at++]=(char)(0x80|((c>>6)&63));out[at++]=(char)(0x80|(c&63));}
 }
 out[at]=0;(*e)->ReleaseStringChars(e,s,p);return accepted(out);
bad:(*e)->ReleaseStringChars(e,s,p);return 0;
}
static jstring to_java(JNIEnv *e,const char *s){
 jchar units[32];unsigned i=0,n=0;if(!accepted(s))return NULL;
 while(s[i]){uint32_t c=(unsigned char)s[i++];unsigned more=0;if(c>=0xf0){more=3;c&=7;}else if(c>=0xe0){more=2;c&=15;}else if(c>=0xc0){more=1;c&=31;}
  while(more--)c=(c<<6)|((unsigned char)s[i++]&63);
  if(c>65535){c-=65536;units[n++]=(jchar)(0xd800|(c>>10));units[n++]=(jchar)(0xdc00|(c&1023));}else units[n++]=(jchar)c;
 }return (*e)->NewString(e,units,(jsize)n);
}
static void changed(JNIEnv *e,jclass cls,jlong token,jstring text,jint confirmed,jlong revision){
 unsigned i;char value[65];oa_name_input *p=NULL;(void)cls;
 if((confirmed!=-1&&confirmed!=0&&confirmed!=1)||revision<0||!from_utf16(e,text,value))return;
 pthread_mutex_lock(&registry_lock);
 for(i=0;i<8;i++)if(registry[i]&&registry[i]->token==(uint64_t)token){p=registry[i];break;}
 if(p){pthread_mutex_lock(&p->lock);
  if(p->active&&((uint64_t)revision>=p->revision)&&!(p->pending&&p->confirmed&&confirmed==0)){
   memcpy(p->value,value,strlen(value)+1);p->revision=(uint64_t)revision;p->confirmed=confirmed;p->pending=1;
  }pthread_mutex_unlock(&p->lock);
 }pthread_mutex_unlock(&registry_lock);
}
oa_name_input *oa_name_input_open(ANativeActivity *activity){
 oa_name_input *p;JNIEnv *e;int detach=0;unsigned i;jclass ac=NULL,loader_class=NULL; jobject loader=NULL,local=NULL;jstring name=NULL;jmethodID method;
 JNINativeMethod native_method={"changed","(JLjava/lang/String;IJ)V",(void*)changed};
 if(!activity||!activity->vm)return NULL;p=(oa_name_input*)calloc(1,sizeof(*p));if(!p)return NULL;
 p->vm=activity->vm;if(pthread_mutex_init(&p->lock,NULL)){free(p);return NULL;}e=environment(p,&detach);if(!e)goto fail;
 p->activity=(*e)->NewGlobalRef(e,activity->clazz);if(!p->activity)goto fail;
 ac=(*e)->GetObjectClass(e,p->activity);method=(*e)->GetMethodID(e,ac,"getClassLoader","()Ljava/lang/ClassLoader;");if(!method||exception(e))goto fail;
 loader=(*e)->CallObjectMethod(e,p->activity,method);if(!loader||exception(e))goto fail;loader_class=(*e)->GetObjectClass(e,loader);
 method=(*e)->GetMethodID(e,loader_class,"loadClass","(Ljava/lang/String;)Ljava/lang/Class;");if(!method||exception(e))goto fail;
 name=(*e)->NewStringUTF(e,"org.opemamalur.scene.TextInput");local=(*e)->CallObjectMethod(e,loader,method,name);if(!local||exception(e))goto fail;
 p->helper=(jclass)(*e)->NewGlobalRef(e,local);if(!p->helper)goto fail;
 p->open=(*e)->GetStaticMethodID(e,p->helper,"open","(Landroid/app/Activity;JLjava/lang/String;)V");if(!p->open||exception(e))goto fail;
 p->sync=(*e)->GetStaticMethodID(e,p->helper,"sync","(Landroid/app/Activity;JLjava/lang/String;J)V");if(!p->sync||exception(e))goto fail;
 p->hide=(*e)->GetStaticMethodID(e,p->helper,"hide","(Landroid/app/Activity;J)V");if(!p->hide||exception(e))goto fail;
 if((*e)->RegisterNatives(e,p->helper,&native_method,1))goto fail;
 pthread_mutex_lock(&registry_lock);for(i=0;i<8;i++)if(!registry[i])break;
 if(i<8){p->token=++next_token;if(!p->token)p->token=++next_token;registry[i]=p;}pthread_mutex_unlock(&registry_lock);
 if(i==8)goto fail;
 if(local)(*e)->DeleteLocalRef(e,local);if(name)(*e)->DeleteLocalRef(e,name);if(loader_class)(*e)->DeleteLocalRef(e,loader_class);if(loader)(*e)->DeleteLocalRef(e,loader);if(ac)(*e)->DeleteLocalRef(e,ac);
 release_env(p,detach);return p;
fail:
 if(e){exception(e);if(local)(*e)->DeleteLocalRef(e,local);if(name)(*e)->DeleteLocalRef(e,name);if(loader_class)(*e)->DeleteLocalRef(e,loader_class);if(loader)(*e)->DeleteLocalRef(e,loader);if(ac)(*e)->DeleteLocalRef(e,ac);if(p->helper)(*e)->DeleteGlobalRef(e,p->helper);if(p->activity)(*e)->DeleteGlobalRef(e,p->activity);release_env(p,detach);}
 pthread_mutex_destroy(&p->lock);free(p);return NULL;
}
int oa_name_input_available(const oa_name_input *p){return p&&p->helper&&p->token;}
int oa_name_input_show(oa_name_input *p,const char *text){
 JNIEnv *e;int detach;jstring s;if(!oa_name_input_available(p)||!accepted(text))return 0;
 oa_name_input_hide(p);pthread_mutex_lock(&registry_lock);p->token=++next_token;if(!p->token)p->token=++next_token;pthread_mutex_unlock(&registry_lock);
 e=environment(p,&detach);if(!e)return 0;s=to_java(e,text);if(!s){release_env(p,detach);return 0;}
 pthread_mutex_lock(&p->lock);p->active=1;p->pending=p->confirmed=0;p->revision=p->delivered=0;strcpy(p->last_sync,text);pthread_mutex_unlock(&p->lock);
 (*e)->CallStaticVoidMethod(e,p->helper,p->open,p->activity,(jlong)p->token,s);(*e)->DeleteLocalRef(e,s);
 if(exception(e)){pthread_mutex_lock(&p->lock);p->active=0;pthread_mutex_unlock(&p->lock);release_env(p,detach);return 0;}
 release_env(p,detach);return 1;
}
void oa_name_input_hide(oa_name_input *p){
 JNIEnv *e;int detach,was;if(!p)return;pthread_mutex_lock(&p->lock);was=p->active;p->active=0;p->pending=0;pthread_mutex_unlock(&p->lock);
 if(!was||!p->helper)return;e=environment(p,&detach);if(!e)return;(*e)->CallStaticVoidMethod(e,p->helper,p->hide,p->activity,(jlong)p->token);exception(e);release_env(p,detach);
}
void oa_name_input_close(oa_name_input *p){
 unsigned i;JNIEnv *e;int detach;if(!p)return;
 pthread_mutex_lock(&registry_lock);for(i=0;i<8;i++)if(registry[i]==p)registry[i]=NULL;pthread_mutex_unlock(&registry_lock);
 oa_name_input_hide(p);e=environment(p,&detach);if(e){if(p->helper)(*e)->DeleteGlobalRef(e,p->helper);if(p->activity)(*e)->DeleteGlobalRef(e,p->activity);release_env(p,detach);}pthread_mutex_destroy(&p->lock);free(p);
}
int oa_name_input_poll(oa_name_input *p,char *out,size_t capacity,int *done){
 int got=0;if(!p||!out||capacity<65||!done)return 0;pthread_mutex_lock(&p->lock);
 if(p->pending){strcpy(out,p->value);strcpy(p->last_sync,p->value);*done=p->confirmed;p->delivered=p->revision;p->pending=0;if(*done)p->active=0;got=1;}
 pthread_mutex_unlock(&p->lock);return got;
}
void oa_name_input_sync(oa_name_input *p,const char *text){
 JNIEnv *e;int detach,send=0;uint64_t acknowledged=0;jstring s;if(!p||!accepted(text))return;
 pthread_mutex_lock(&p->lock);if(p->active&&strcmp(text,p->last_sync)){strcpy(p->last_sync,text);acknowledged=p->delivered;send=1;}pthread_mutex_unlock(&p->lock);if(!send)return;
 e=environment(p,&detach);if(!e)return;s=to_java(e,text);if(s){(*e)->CallStaticVoidMethod(e,p->helper,p->sync,p->activity,(jlong)p->token,s,(jlong)acknowledged);(*e)->DeleteLocalRef(e,s);}exception(e);release_env(p,detach);
}
#endif
