#include "scene_material_renderer_v09.h"
#include <stdio.h>
#include <string.h>
static int fail(char *error,size_t capacity,const char *message){if(error&&capacity)snprintf(error,capacity,"%s",message);return 0;}
void scene_material_renderer_v09_close(scene_material_renderer_v09 *r){if(!r)return;if(r->uv_buffer)glDeleteBuffers(1,&r->uv_buffer);if(r->texture_count)glDeleteTextures((GLsizei)r->texture_count,r->textures);memset(r,0,sizeof(*r));}
int scene_material_renderer_v09_open(scene_material_renderer_v09 *r,const scene_materials_v09 *m,GLuint vao,char *error,size_t capacity){
    uint32_t i;GLint maximum=0;size_t total;
    if(error&&capacity)*error=0;
    if(!r||!m||!vao||!m->uv||!m->draws||!m->vertex_count||m->texture_count>SCENE_MATERIALS_V09_MAX_TEXTURES||r->ready||r->uv_buffer||r->texture_count)return fail(error,capacity,"Material renderer requires loaded package and empty renderer");
    total=(size_t)m->vertex_count*8;glGetIntegerv(GL_MAX_TEXTURE_SIZE,&maximum);
    if(maximum<1)return fail(error,capacity,"Material renderer texture limit unavailable");
    for(i=0;i<m->texture_count;i++){
        uint32_t w=m->textures[i].width,h=m->textures[i].height;
        if(w>(uint32_t)maximum||h>(uint32_t)maximum)return fail(error,capacity,"Material texture exceeds device dimension cap");
        for(;;){size_t n=(size_t)w*h*4;if(n>SCENE_MATERIALS_V09_MAX_BYTES-total)return fail(error,capacity,"Material GPU byte budget exceeded");total+=n;if(w==1&&h==1)break;if(w>1)w/=2;if(h>1)h/=2;}
    }
    r->vertex_count=m->vertex_count;r->draw_count=m->draw_count;r->gpu_bytes=total;
    glBindVertexArray(vao);glGenBuffers(1,&r->uv_buffer);glBindBuffer(GL_ARRAY_BUFFER,r->uv_buffer);
    glBufferData(GL_ARRAY_BUFFER,(GLsizeiptr)((size_t)m->vertex_count*8),m->uv,GL_STATIC_DRAW);
    glEnableVertexAttribArray(3);glVertexAttribPointer(3,2,GL_FLOAT,GL_FALSE,8,(const void*)0);
    glBindVertexArray(0);glBindBuffer(GL_ARRAY_BUFFER,0);
    r->texture_count=m->texture_count;if(r->texture_count)glGenTextures((GLsizei)r->texture_count,r->textures);
    glActiveTexture(GL_TEXTURE0);glPixelStorei(GL_UNPACK_ALIGNMENT,1);
    for(i=0;i<r->texture_count;i++){
        const scene_material_texture_v09 *t=m->textures+i;
        glBindTexture(GL_TEXTURE_2D,r->textures[i]);
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT);
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR_MIPMAP_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);
        glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,(GLsizei)t->width,(GLsizei)t->height,0,GL_RGBA,GL_UNSIGNED_BYTE,t->rgba);glGenerateMipmap(GL_TEXTURE_2D);
        if(glGetError()!=GL_NO_ERROR)goto failed;
    }
    glBindTexture(GL_TEXTURE_2D,0);glPixelStorei(GL_UNPACK_ALIGNMENT,4);
    if(!r->uv_buffer||glGetError()!=GL_NO_ERROR)goto failed;r->ready=1;return 1;
failed:
    glBindVertexArray(vao);glDisableVertexAttribArray(3);glBindVertexArray(0);
    glBindTexture(GL_TEXTURE_2D,0);glPixelStorei(GL_UNPACK_ALIGNMENT,4);scene_material_renderer_v09_close(r);
    return fail(error,capacity,"Material GLES allocation/upload failed");
}
int scene_material_renderer_v09_draw(const scene_material_renderer_v09 *r,const scene_materials_v09 *m,GLint has_texture,GLint sampler){
    uint32_t i;
    if(!r||!r->ready||!m||m->vertex_count!=r->vertex_count||m->draw_count!=r->draw_count||m->texture_count!=r->texture_count||has_texture<0||sampler<0)return 0;
    glActiveTexture(GL_TEXTURE0);glUniform1i(sampler,0);
    for(i=0;i<m->draw_count;i++){
        const scene_material_draw_v09 *d=m->draws+i;int textured=d->texture_index!=SCENE_MATERIALS_V09_FALLBACK;
        if(textured&&d->texture_index>=r->texture_count)return 0;
        glUniform1i(has_texture,textured);glBindTexture(GL_TEXTURE_2D,textured?r->textures[d->texture_index]:0);
        glDrawArrays(GL_TRIANGLES,(GLint)d->first_vertex,(GLsizei)d->vertex_count);
    }
    glBindTexture(GL_TEXTURE_2D,0);glUniform1i(has_texture,0);return glGetError()==GL_NO_ERROR;
}
