#ifndef OA_CACHE_TEST_GL_H
#define OA_CACHE_TEST_GL_H
typedef unsigned GLuint;typedef int GLint;typedef unsigned GLenum;
#define GL_TEXTURE0 0x84c0
#define GL_TEXTURE_2D 0xde1
GLint glGetUniformLocation(GLuint,const char*);
void glActiveTexture(GLenum);
void glBindTexture(GLenum,GLuint);
#endif
