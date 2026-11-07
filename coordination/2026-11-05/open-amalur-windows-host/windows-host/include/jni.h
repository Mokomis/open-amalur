#ifndef OA_WIN_JNI_H
#define OA_WIN_JNI_H
typedef int jint;typedef void JNIEnv;
#define JNI_OK 0
#define JNI_EDETACHED -2
#define JNI_VERSION_1_6 0x10006
struct oa_jvm;
typedef const struct oa_jvm *JavaVM;
struct oa_jvm{jint(*GetEnv)(JavaVM*,void**,jint);jint(*AttachCurrentThread)(JavaVM*,JNIEnv**,void*);jint(*DetachCurrentThread)(JavaVM*);};
#endif
