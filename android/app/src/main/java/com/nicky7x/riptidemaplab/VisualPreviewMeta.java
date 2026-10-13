package com.nicky7x.riptidemaplab;

import org.json.JSONArray;
import org.json.JSONObject;
import org.json.JSONException;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** UVs and material groups associated with a previously validated static model. */
final class VisualPreviewMeta {
    private VisualPreviewMeta(){}
    static final class Result {
        final byte[] uv;
        final JSONArray groups,materials;
        final LinkedHashSet<String> used;
        Result(byte[] u,JSONArray g,JSONArray m,LinkedHashSet<String> paths){uv=u;groups=g;materials=m;used=paths;}
    }
    static Result parse(byte[] data) throws IOException {
        try {return decode(data);}catch(JSONException|IndexOutOfBoundsException e){throw new IOException("Metadados UV inválidos",e);}
    }
    private static Result decode(byte[] data) throws IOException,JSONException {
        if(data.length<64)throw new IOException("Modelo truncado");
        ByteBuffer b=ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);
        int p=46,n=b.getInt(p);p+=4;
        if(n<1||n>256)throw new IOException("Materiais inválidos");
        String[] mats=new String[n];JSONArray materials=new JSONArray();
        for(int i=0;i<n;i++){
            int q=p;while(q<data.length&&q-p<512&&data[q]!=0)q++;
            if(q==p||q>=data.length||q-p>=512)throw new IOException("Nome de material inválido");
            mats[i]=new String(data,p,q-p,StandardCharsets.UTF_8);materials.put(mats[i]);p=q+1;
        }
        if(p+4>data.length)throw new IOException("Grupo de material truncado");
        int gc=b.getInt(p);p+=4;
        if(gc<1||gc>8192||48L*gc>data.length-p)throw new IOException("Grupos visuais não reconhecidos");
        int[][] groups=new int[gc][4];
        for(int g=0;g<gc;g++){
            for(int a=0;a<4;a++)groups[g][a]=b.getInt(p+4*a);
            if(groups[g][1]<0||groups[g][1]>=n)throw new IOException("Material ausente");
            p+=48;
        }
        if(p+8>data.length)throw new IOException("Streams truncados");
        int unknown=b.getInt(p),sc=b.getInt(p+4);p+=8;
        if(unknown!=0||sc<1||sc>64)throw new IOException("Tabela de streams inválida");
        int[] indexOffsets=new int[sc],counts=new int[sc];int sum=0;
        java.io.ByteArrayOutputStream uvs=new java.io.ByteArrayOutputStream();
        for(int st=0;st<sc;st++){
            if(p+8>data.length)throw new IOException("Stream truncado");
            int stride=b.getInt(p),len=b.getInt(p+4);p+=8;
            if(stride<12||stride>128||len<0||len%stride!=0||len>data.length-p)
                throw new IOException("Vértices inválidos");
            int count=len/stride,offset=uvOffset(stride);
            for(int i=0;i<count;i++){
                float u=0,v=0;
                if(offset>=12&&offset+8<=stride){
                    u=b.getFloat(p+i*stride+offset);v=b.getFloat(p+i*stride+offset+4);
                    if(!Float.isFinite(u)||!Float.isFinite(v)||Math.abs(u)>1e6||Math.abs(v)>1e6){u=0;v=0;}
                }
                int ub=Float.floatToIntBits(u),vb=Float.floatToIntBits(v);
                for(int k=0;k<4;k++)uvs.write((ub>>>(8*k))&255);
                for(int k=0;k<4;k++)uvs.write((vb>>>(8*k))&255);
            }
            p+=len;
            if(p+4>data.length)throw new IOException("Índices inválidos");
            int ic=b.getInt(p);p+=4;
            if(ic<0||ic>900000||2L*ic>data.length-p)throw new IOException("Índices fora da malha");
            indexOffsets[st]=sum;counts[st]=ic;sum+=ic;p+=ic*2;
        }
        JSONArray out=new JSONArray();LinkedHashSet<String> used=new LinkedHashSet<>();
        for(int[] g:groups){
            int st=g[0],mat=g[1],start=g[2],tri=g[3];
            if(st<0||st>=sc||start<0||tri<0||start+3L*tri>counts[st])throw new IOException("Grupo fora do stream");
            String material=mats[mat];used.add(material);
            JSONObject x=new JSONObject();x.put("start",indexOffsets[st]+start);x.put("count",tri*3);x.put("material",material);
            out.put(x);
        }
        return new Result(uvs.toByteArray(),out,materials,used);
    }
    static int uvOffset(int stride){
        switch(stride){case 20:return 12;case 24:return 16;case 28:return 16;case 32:return 20;case 36:return 24;default:return -1;}
    }
}