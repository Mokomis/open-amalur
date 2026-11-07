#include "oa_ui_text_android.h"
#include "oa_ui_text_utf16.h"
#include "oa_ui_text_pixels.h"
#include <android/bitmap.h>
#include <android/log.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
struct oa_ui_text_android_context {
 JavaVM *vm;jobject activity;jclass helper,result_class;
 jmethodID render,recycle,is_premultiplied,has_alpha;
 jfieldID bitmap,advance,origin_x,origin_y;
};
typedef struct env_scope{JNIEnv*env;int attached;}env_scope;
static int enter(JavaVM*vm,env_scope*s){
 jint rc;memset(s,0,sizeof(*s));if(!vm)return 0;
 rc=(*vm)->GetEnv(vm,(void**)&s->env,JNI_VERSION_1_6);
 if(rc==JNI_OK)return 1;
 if(rc!=JNI_EDETACHED||(*vm)->AttachCurrentThread(vm,&s->env,NULL)!=JNI_OK)return 0;
 s->attached=1;return 1;
}
static void leave(JavaVM*vm,env_scope*s){if(s->attached)(*vm)->DetachCurrentThread(vm);}
static int clear_exception(JNIEnv*e){if((*e)->ExceptionCheck(e)){(*e)->ExceptionClear(e);return 1;}return 0;}
static jclass load_class(JNIEnv*e,jobject loader,jmethodID load,const char*ascii){
 jstring name=(*e)->NewStringUTF(e,ascii);jclass c;
 if(!name||(*e)->ExceptionCheck(e))return NULL;
 c=(jclass)(*e)->CallObjectMethod(e,loader,load,name);(*e)->DeleteLocalRef(e,name);
 return (*e)->ExceptionCheck(e)?NULL:c;
}
static void pixels_free(void*u,uint8_t*p){(void)u;free(p);}
void oa_ui_text_android_close(oa_ui_text_android_context*c){
 env_scope s;if(!c)return;
 if(enter(c->vm,&s)){JNIEnv*e=s.env;
  if(c->activity)(*e)->DeleteGlobalRef(e,c->activity);
  if(c->helper)(*e)->DeleteGlobalRef(e,c->helper);
  if(c->result_class)(*e)->DeleteGlobalRef(e,c->result_class);
  leave(c->vm,&s);
 }free(c);
}
oa_ui_text_android_context *oa_ui_text_android_open(ANativeActivity*a){
 oa_ui_text_android_context*c=NULL;env_scope s;JNIEnv*e;
 jclass ac,lc,h,rc,bc;jobject loader;jmethodID get_loader,load;
 int frame=0,ok=0;if(!a||!a->vm||!a->clazz||!enter(a->vm,&s))return NULL;e=s.env;
 if((*e)->ExceptionCheck(e)){leave(a->vm,&s);return NULL;}
 if((*e)->PushLocalFrame(e,32)<0)goto done;frame=1;
 c=(oa_ui_text_android_context*)calloc(1,sizeof(*c));if(!c)goto done;c->vm=a->vm;
 ac=(*e)->GetObjectClass(e,a->clazz);if(!ac||(*e)->ExceptionCheck(e))goto done;
 get_loader=(*e)->GetMethodID(e,ac,"getClassLoader","()Ljava/lang/ClassLoader;");
 if(!get_loader||(*e)->ExceptionCheck(e))goto done;
 loader=(*e)->CallObjectMethod(e,a->clazz,get_loader);if(!loader||(*e)->ExceptionCheck(e))goto done;
 lc=(*e)->GetObjectClass(e,loader);if(!lc||(*e)->ExceptionCheck(e))goto done;
 load=(*e)->GetMethodID(e,lc,"loadClass","(Ljava/lang/String;)Ljava/lang/Class;");
 if(!load||(*e)->ExceptionCheck(e))goto done;
 h=load_class(e,loader,load,"org.opemamalur.scene.TextRasterizer");if(!h)goto done;
 rc=load_class(e,loader,load,"org.opemamalur.scene.TextRasterizer$Result");if(!rc)goto done;
 bc=load_class(e,loader,load,"android.graphics.Bitmap");if(!bc)goto done;
 c->render=(*e)->GetStaticMethodID(e,h,"render","(Landroid/app/Activity;Ljava/lang/String;II)Lorg/opemamalur/scene/TextRasterizer$Result;");
 if(!c->render||(*e)->ExceptionCheck(e))goto done;
 c->bitmap=(*e)->GetFieldID(e,rc,"bitmap","Landroid/graphics/Bitmap;");if(!c->bitmap||(*e)->ExceptionCheck(e))goto done;
 c->advance=(*e)->GetFieldID(e,rc,"advance","F");if(!c->advance||(*e)->ExceptionCheck(e))goto done;
 c->origin_x=(*e)->GetFieldID(e,rc,"originX","F");if(!c->origin_x||(*e)->ExceptionCheck(e))goto done;
 c->origin_y=(*e)->GetFieldID(e,rc,"originY","F");if(!c->origin_y||(*e)->ExceptionCheck(e))goto done;
 c->recycle=(*e)->GetMethodID(e,bc,"recycle","()V");if(!c->recycle||(*e)->ExceptionCheck(e))goto done;
 c->is_premultiplied=(*e)->GetMethodID(e,bc,"isPremultiplied","()Z");if(!c->is_premultiplied||(*e)->ExceptionCheck(e))goto done;
 c->has_alpha=(*e)->GetMethodID(e,bc,"hasAlpha","()Z");if(!c->has_alpha||(*e)->ExceptionCheck(e))goto done;
 c->activity=(*e)->NewGlobalRef(e,a->clazz);if(!c->activity||(*e)->ExceptionCheck(e))goto done;
 c->helper=(jclass)(*e)->NewGlobalRef(e,h);if(!c->helper||(*e)->ExceptionCheck(e))goto done;
 c->result_class=(jclass)(*e)->NewGlobalRef(e,rc);if(!c->result_class||(*e)->ExceptionCheck(e))goto done;
 ok=1;
done:
 if(clear_exception(e))ok=0;
 if(frame)(*e)->PopLocalFrame(e,NULL);leave(a->vm,&s);
 if(!ok){oa_ui_text_android_close(c);__android_log_print(ANDROID_LOG_WARN,"OpemText","TextRasterizer helper initialization failed");return NULL;}
 return c;
}
int oa_ui_text_android(void*user,int font,unsigned px,const char*utf8,oa_ui_text_bitmap*out){
 oa_ui_text_android_context*c=(oa_ui_text_android_context*)user;
 env_scope s;JNIEnv*e;jchar wide[512];size_t wn=0,bytes;
 jstring text;jobject result=NULL,bitmap=NULL;AndroidBitmapInfo info;
 void*locked=NULL;uint8_t*rgba=NULL;float advance=0,ox=0,oy=0;
 int frame=0,pixels_locked=0,ok=0;jboolean premul,alpha;
 if(!out)return 0;memset(out,0,sizeof(*out));
 if(!c||font<0||font>1||px<1||px>256||
  !oa_ui_android_utf16(utf8,(uint16_t*)wide,512,&wn)||!enter(c->vm,&s))return 0;
 e=s.env;if((*e)->ExceptionCheck(e)){leave(c->vm,&s);return 0;}
 if((*e)->PushLocalFrame(e,24)<0)goto done;frame=1;
 /* Actual Unicode scalars encoded to UTF16; NewStringUTF uses MODIFIED UTF8
    and is intentionally not used for user text/non-BMP characters. */
 text=(*e)->NewString(e,wide,(jsize)wn);if(!text||(*e)->ExceptionCheck(e))goto done;
 result=(*e)->CallStaticObjectMethod(e,c->helper,c->render,c->activity,text,(jint)font,(jint)px);
 if(!result||(*e)->ExceptionCheck(e))goto done;
 bitmap=(*e)->GetObjectField(e,result,c->bitmap);if(!bitmap||(*e)->ExceptionCheck(e))goto done;
 advance=(*e)->GetFloatField(e,result,c->advance);if((*e)->ExceptionCheck(e))goto done;
 ox=(*e)->GetFloatField(e,result,c->origin_x);if((*e)->ExceptionCheck(e))goto done;
 oy=(*e)->GetFloatField(e,result,c->origin_y);
 if((*e)->ExceptionCheck(e)||!isfinite(advance)||advance<0||advance>8192||
  !isfinite(ox)||!isfinite(oy)||fabsf(ox)>4096||fabsf(oy)>4096)goto done;
 memset(&info,0,sizeof info);
 if(AndroidBitmap_getInfo(e,bitmap,&info)!=ANDROID_BITMAP_RESULT_SUCCESS||(*e)->ExceptionCheck(e)||
  info.format!=ANDROID_BITMAP_FORMAT_RGBA_8888||!info.width||!info.height||
  info.width>4096||info.height>4096||(size_t)info.width*info.height>1024*1024||
  info.stride<info.width*4)goto done;
 /* info.flags is only populated since API30. Query Java state for API26+
    instead; never assume premultiplication from a Vulkan/GLES format. */
 premul=(*e)->CallBooleanMethod(e,bitmap,c->is_premultiplied);if((*e)->ExceptionCheck(e))goto done;
 alpha=(*e)->CallBooleanMethod(e,bitmap,c->has_alpha);if((*e)->ExceptionCheck(e))goto done;
 {
  int status=AndroidBitmap_lockPixels(e,bitmap,&locked);
  pixels_locked=status==ANDROID_BITMAP_RESULT_SUCCESS;
  if(!pixels_locked||!locked||(*e)->ExceptionCheck(e))goto done;
 }bytes=(size_t)info.width*info.height*4;rgba=(uint8_t*)malloc(bytes);if(!rgba)goto done;
 oa_ui_android_straight_rgba(rgba,(const uint8_t*)locked,info.width,info.height,info.stride,premul,alpha);
 ok=1;
done:
 if(clear_exception(e))ok=0;
 if(pixels_locked){if(AndroidBitmap_unlockPixels(e,bitmap)!=ANDROID_BITMAP_RESULT_SUCCESS)ok=0;if(clear_exception(e))ok=0;}
 if(bitmap){(*e)->CallVoidMethod(e,bitmap,c->recycle);if(clear_exception(e))ok=0;}
 if(frame)(*e)->PopLocalFrame(e,NULL);
 leave(c->vm,&s);
 if(!ok){free(rgba);return 0;}
 out->rgba=rgba;out->width=info.width;out->height=info.height;out->advance=advance;
 out->origin_x=ox;out->origin_y=oy;out->release=pixels_free;return 1;
}
