"""Batched 2D UI: one rectangle draw and one font-atlas draw per frame.

Pillow rasterizes the atlas once. OpenGL resources stay on the window's thread.
"""
from math import ceil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from OpenGL import GL


class Canvas:
    def __init__(self, pixel_ratio=1):
        ratio = min(2, max(1, ceil(pixel_ratio)))
        font = ImageFont.load_default(size=14*ratio)
        cell = 32*ratio
        atlas = Image.new('RGBA', (16*cell, 6*cell), (255,255,255,0))
        draw = ImageDraw.Draw(atlas)
        self.glyphs = {}
        for i, code in enumerate(range(32,127)):
            char=chr(code)
            x,y=(i%16)*cell,(i//16)*cell
            draw.text((x+4*ratio,y+18*ratio),char,font=font,fill='white',anchor='ls')
            self.glyphs[char]=(x/atlas.width,y/atlas.height,(x+cell)/atlas.width,
                               (y+cell)/atlas.height,font.getlength(char)/ratio)
        self.texture=GL.glGenTextures(1)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D,self.texture)
        GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_LINEAR)
        GL.glTexImage2D(GL.GL_TEXTURE_2D,0,GL.GL_RGBA,atlas.width,atlas.height,0,
                        GL.GL_RGBA,GL.GL_UNSIGNED_BYTE,atlas.tobytes())
        self.image_textures={}
        self.pixel_textures={}
        self.begin()

    def begin(self):
        self.clip=None
        self.rects=[]
        self.letters=[]
        self.images=[]

    def rect(self,x,y,w,h,color):
        if self.clip:
            cx,cy,cw,ch=self.clip
            right,bottom=min(x+w,cx+cw),min(y+h,cy+ch)
            x,y=max(x,cx),max(y,cy);w,h=right-x,bottom-y
            if w<=0 or h<=0:return
        rgba=(*color,1.) if len(color)==3 else color
        for vx,vy in ((x,y),(x+w,y),(x+w,y+h),(x,y+h)):
            self.rects.append((vx,vy,*rgba))

    def polygon(self,points,color):
        if self.clip:
            cx,cy,cw,ch=self.clip
            for axis,bound,sign in ((0,cx,1),(0,cx+cw,-1),(1,cy,1),(1,cy+ch,-1)):
                output=[]
                for a,b in zip(points,(*points[1:],points[0]) if len(points) else ()):
                    inside_a=(a[axis]-bound)*sign>=0;inside_b=(b[axis]-bound)*sign>=0
                    if inside_a:output.append(a)
                    if inside_a!=inside_b:
                        t=(bound-a[axis])/(b[axis]-a[axis])
                        output.append(tuple(a[i]+t*(b[i]-a[i]) for i in range(2)))
                points=output
        rgba=(*color,1.) if len(color)==3 else color
        for i in range(1,len(points)-1):
            for x,y in (points[0],points[i],points[i+1],points[i+1]):
                self.rects.append((x,y,*rgba))

    def line(self,x1,y1,x2,y2,width,color):
        length=max(.001,((x2-x1)**2+(y2-y1)**2)**.5)
        dx=-(y2-y1)*width/(2*length);dy=(x2-x1)*width/(2*length)
        self.polygon(((x1+dx,y1+dy),(x2+dx,y2+dy),(x2-dx,y2-dy),(x1-dx,y1-dy)),color)

    def width(self,text,size=14):
        return sum(self.glyphs.get(c,self.glyphs['?'])[4] for c in text)*size/14

    def text(self,text,x,y,color=(.86,.89,.91),size=14,max_width=None):
        scale=size/14
        rgba=(*color,1.) if len(color)==3 else color
        if max_width is not None:
            while text and self.width(text,size)>max_width:
                text=text[:-1]
        for char in text:
            u,v,u2,v2,advance=self.glyphs.get(char,self.glyphs['?'])
            if char!=' ':
                x1,y1=x-4*scale,y-4*scale
                x2,y2=x1+32*scale,y1+32*scale
                if self.clip:
                    cx,cy,cw,ch=self.clip
                    nx,ny=max(x1,cx),max(y1,cy);rx,ry=min(x2,cx+cw),min(y2,cy+ch)
                    if rx<=nx or ry<=ny:
                        x+=advance*scale
                        continue
                    u,u2=u+(u2-u)*(nx-x1)/(x2-x1),u+(u2-u)*(rx-x1)/(x2-x1)
                    v,v2=v+(v2-v)*(ny-y1)/(y2-y1),v+(v2-v)*(ry-y1)/(y2-y1)
                    x1,y1,x2,y2=nx,ny,rx,ry
                for px,py,tx,ty in ((x1,y1,u,v),(x2,y1,u2,v),(x2,y2,u2,v2),(x1,y2,u,v2)):
                    self.letters.append((px,py,tx,ty,*rgba))
            x+=advance*scale

    def image(self,path,x,y,w,h):
        key=str(path)
        if key not in self.image_textures:
            with Image.open(path) as source:bitmap=source.convert('RGBA')
            tex=GL.glGenTextures(1);GL.glBindTexture(GL.GL_TEXTURE_2D,tex)
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,GL.GL_LINEAR)
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_LINEAR)
            GL.glTexImage2D(GL.GL_TEXTURE_2D,0,GL.GL_RGBA,bitmap.width,bitmap.height,0,GL.GL_RGBA,GL.GL_UNSIGNED_BYTE,bitmap.tobytes())
            self.image_textures[key]=tex
        left,top,right,bottom=x,y,x+w,y+h
        if self.clip:
            cx,cy,cw,ch=self.clip
            left,top,right,bottom=max(left,cx),max(top,cy),min(right,cx+cw),min(bottom,cy+ch)
        if right<=left or bottom<=top:return
        u,v,u2,v2=(left-x)/w,(top-y)/h,(right-x)/w,(bottom-y)/h
        self.images.append((self.image_textures[key],((left,top,u,v),(right,top,u2,v),(right,bottom,u2,v2),(left,bottom,u,v2))))

    def pixels(self,key,rgb,x,y,w,h,version=0):
        """An RGB array (rows x columns x 3, top row first) drawn into a rectangle, each pixel
        a sharp square; uploaded again only when `version` changes."""
        rgb=np.ascontiguousarray(rgb,dtype=np.uint8)
        tex,shown=self.pixel_textures.get(key,(None,None))
        if tex is None:
            tex=GL.glGenTextures(1);GL.glBindTexture(GL.GL_TEXTURE_2D,tex)
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,GL.GL_NEAREST)
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_NEAREST)
        if shown!=version:
            GL.glBindTexture(GL.GL_TEXTURE_2D,tex)
            GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT,1)
            GL.glTexImage2D(GL.GL_TEXTURE_2D,0,GL.GL_RGB,rgb.shape[1],rgb.shape[0],0,GL.GL_RGB,GL.GL_UNSIGNED_BYTE,rgb.tobytes())
        self.pixel_textures[key]=(tex,version)
        self.images.append((tex,((x,y,0.,0.),(x+w,y,1.,0.),(x+w,y+h,1.,1.),(x,y+h,0.,1.))))

    def flush(self,width,height,framebuffer_width,framebuffer_height):
        GL.glPushAttrib(GL.GL_ALL_ATTRIB_BITS)
        GL.glPushClientAttrib(GL.GL_CLIENT_ALL_ATTRIB_BITS)
        GL.glViewport(0,0,framebuffer_width,framebuffer_height)
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDisable(GL.GL_LIGHTING)
        GL.glDisable(GL.GL_CULL_FACE)
        GL.glDisable(GL.GL_SCISSOR_TEST)
        GL.glDisable(GL.GL_ALPHA_TEST)
        GL.glDisable(GL.GL_FOG)
        for unit in (GL.GL_TEXTURE1, GL.GL_TEXTURE2):
            GL.glActiveTexture(unit)
            GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glClientActiveTexture(GL.GL_TEXTURE0)
        for coordinate in (GL.GL_TEXTURE_GEN_S,GL.GL_TEXTURE_GEN_T,GL.GL_TEXTURE_GEN_R,GL.GL_TEXTURE_GEN_Q):
            GL.glDisable(coordinate)
        GL.glMatrixMode(GL.GL_TEXTURE)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA,GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glOrtho(0,width,height,0,-1,1)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glEnableClientState(GL.GL_COLOR_ARRAY)
        GL.glDisable(GL.GL_TEXTURE_2D)
        if self.rects:
            array=np.asarray(self.rects,dtype=np.float32)
            positions=np.ascontiguousarray(array[:,:2])
            colors=np.ascontiguousarray(array[:,2:])
            GL.glVertexPointer(2,GL.GL_FLOAT,0,positions)
            GL.glColorPointer(4,GL.GL_FLOAT,0,colors)
            GL.glDrawArrays(GL.GL_QUADS,0,len(array))
        if self.images:
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glTexEnvi(GL.GL_TEXTURE_ENV,GL.GL_TEXTURE_ENV_MODE,GL.GL_MODULATE)
            GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
            for tex,vertices in self.images:
                array=np.asarray([(*v,1.,1.,1.,1.) for v in vertices],dtype=np.float32)
                positions=np.ascontiguousarray(array[:,:2]);uv=np.ascontiguousarray(array[:,2:4]);colors=np.ascontiguousarray(array[:,4:])
                GL.glBindTexture(GL.GL_TEXTURE_2D,tex)
                GL.glVertexPointer(2,GL.GL_FLOAT,0,positions);GL.glTexCoordPointer(2,GL.GL_FLOAT,0,uv);GL.glColorPointer(4,GL.GL_FLOAT,0,colors)
                GL.glDrawArrays(GL.GL_QUADS,0,4)
        if self.letters:
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D,self.texture)
            GL.glTexEnvi(GL.GL_TEXTURE_ENV,GL.GL_TEXTURE_ENV_MODE,GL.GL_MODULATE)
            GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
            array=np.asarray(self.letters,dtype=np.float32)
            positions=np.ascontiguousarray(array[:,:2])
            uv=np.ascontiguousarray(array[:,2:4])
            colors=np.ascontiguousarray(array[:,4:])
            GL.glVertexPointer(2,GL.GL_FLOAT,0,positions)
            GL.glTexCoordPointer(2,GL.GL_FLOAT,0,uv)
            GL.glColorPointer(4,GL.GL_FLOAT,0,colors)
            GL.glDrawArrays(GL.GL_QUADS,0,len(array))
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_TEXTURE)
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPopClientAttrib()
        GL.glPopAttrib()

    def close(self):
        GL.glDeleteTextures([self.texture,*self.image_textures.values(),*(t for t,_ in self.pixel_textures.values())])
