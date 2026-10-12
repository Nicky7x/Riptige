package com.nicky7x.riptidemaplab;

import org.json.JSONObject;
import org.tukaani.xz.LZMAInputStream;

import java.io.*;
import java.nio.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.*;
import android.util.Base64;

/** Read-only importer of user-supplied APF v6 resources. No game data is shipped in APK. */
public final class ApfImporter {
    private static final String PREFIX = "VuCollisionMeshAsset/Level/";
    private static final int MAX_RESOURCE = 64 * 1024 * 1024;
    private static final int MAX_INDEX = 100 * 1024 * 1024;
    private ApfImporter() {}

    public static final class Result {
        public final String json;
        public final int arenas, meshes, skipped;
        public Result(String json, int arenas, int meshes, int skipped) {
            this.json=json;this.arenas=arenas;this.meshes=meshes;this.skipped=skipped;
        }
    }
    private static final class Entry {
        final String name;
        final long offset;
        final int usize, csize, flags;
        Entry(String n,long o,int u,int c,int f) { name=n;offset=o;usize=u;csize=c;flags=f; }
    }

    public static void extractAssetArchive(File xapk, File apf) throws IOException {
        File base = File.createTempFile("riptide-base-", ".apk", xapk.getParentFile());
        try {
            try (ZipFile zip = new ZipFile(xapk)) {
                ZipEntry root = zip.getEntry("base.apk");
                if(root==null) throw new IOException("Este arquivo não possui base.apk");
                if(root.getSize()>250L*1024*1024) throw new IOException("APK excede limite de segurança");
                try(InputStream in=zip.getInputStream(root);OutputStream out=new BufferedOutputStream(new FileOutputStream(base))) {
                    copyLimited(in,out,250L*1024*1024);
                }
            }
            try(ZipFile zip=new ZipFile(base)) {
                ZipEntry item=zip.getEntry("assets/Assets.apf");
                if(item==null)throw new IOException("assets/Assets.apf não encontrado");
                if(item.getSize()>350L*1024*1024)throw new IOException("APF excede limite de segurança");
                try(InputStream in=zip.getInputStream(item);OutputStream out=new BufferedOutputStream(new FileOutputStream(apf))) {
                    copyLimited(in,out,350L*1024*1024);
                }
            }
        } finally { if(!base.delete())base.deleteOnExit(); }
    }

    public static Result importApf(File apf) throws IOException {
        JSONObject arenas=new JSONObject();
        int skipped=0,meshes=0;
        try(RandomAccessFile file=new RandomAccessFile(apf,"r")) {
            if(file.length()<60)throw new IOException("APF muito curto");
            byte[] hdr=new byte[60]; file.readFully(hdr);
            if(!"FPUV".equals(new String(hdr,0,4, StandardCharsets.US_ASCII)))throw new IOException("Assinatura APF desconhecida");
            ByteBuffer h=ByteBuffer.wrap(hdr).order(ByteOrder.LITTLE_ENDIAN);
            int version=h.getInt(4); long indexPos=Integer.toUnsignedLong(h.getInt(8));
            long n=Integer.toUnsignedLong(h.getInt(12)); long indexBytes=Integer.toUnsignedLong(h.getInt(16));
            if(version!=6)throw new IOException("Formato APF ainda não suportado: "+version);
            if(n>250_000||indexBytes>MAX_INDEX||indexPos<60||indexPos+indexBytes>file.length())
                throw new IOException("Índice APF inválido");
            byte[] idx=new byte[(int)indexBytes];file.seek(indexPos);file.readFully(idx);
            ByteBuffer ib=ByteBuffer.wrap(idx).order(ByteOrder.LITTLE_ENDIAN);
            List<Entry> entries=new ArrayList<>();
            int p=0;
            for(int i=0;i<n;i++) {
                int end=p; while(end<idx.length&&idx[end]!=0)end++;
                if(end>=idx.length||end-p>4096||end+1+20>idx.length)throw new IOException("Índice incompleto na entrada "+i);
                String name=new String(idx,p,end-p,StandardCharsets.UTF_8);
                p=end+1;
                long off=Integer.toUnsignedLong(ib.getInt(p));
                long usize=Integer.toUnsignedLong(ib.getInt(p+4));
                long csize=Integer.toUnsignedLong(ib.getInt(p+8));
                int flags=ib.getInt(p+16); p+=20;
                if(off<60||csize>indexPos-off)throw new IOException("Entrada fora do APF: "+name);
                if(name.startsWith(PREFIX)) {
                    if(usize>MAX_RESOURCE||csize>MAX_RESOURCE){skipped++;continue;}
                    entries.add(new Entry(name,off,(int)usize,(int)csize,flags));
                }
            }
            if(p!=idx.length)throw new IOException("Bytes desconhecidos no índice APF");
            for(Entry e:entries) {
                try {
                    byte[] raw=new byte[e.csize];file.seek(e.offset);file.readFully(raw);
                    byte[] mesh=unpack(raw,e.usize,e.flags);
                    int[] info=checkMesh(mesh);
                    String suffix=e.name.substring(PREFIX.length());
                    int slash=suffix.indexOf('/');if(slash<1||slash==suffix.length()-1)throw new IOException("Nome inválido");
                    String arena=suffix.substring(0,slash),section=suffix.substring(slash+1);
                    JSONObject zones=arenas.optJSONObject(arena);
                    if(zones==null){zones=new JSONObject();arenas.put(arena,zones);}
                    JSONObject rec=new JSONObject();
                    rec.put("blob", gzipBase64(mesh));rec.put("size",mesh.length);
                    rec.put("vertices",info[0]);rec.put("triangles",info[1]);rec.put("source",e.name);
                    zones.put(section,rec);meshes++;
                } catch(Exception err) { skipped++; }
            }
        }
        if(meshes==0)throw new IOException("Não encontrei malhas compatíveis nesse XAPK");
        return new Result(arenas.toString(),arenas.length(),meshes,skipped);
    }

    static byte[] unpack(byte[] data,int expected,int flags) throws IOException {
        if(expected<0||expected>MAX_RESOURCE)throw new IOException("Tamanho fora do limite");
        int kind=flags>>>16;
        if(kind==0) {
            if(data.length!=expected)throw new IOException("Tamanho da malha não confere");
            return data;
        }
        InputStream input;
        if(kind==1) input=new InflaterInputStream(new ByteArrayInputStream(data));
        else if(kind==2) {
            if(data.length<6)throw new IOException("Payload LZMA inválido");
            long dict=ByteBuffer.wrap(data,1,4).order(ByteOrder.LITTLE_ENDIAN).getInt() & 0xffffffffL;
            if(dict<4096||dict>128L*1024*1024)throw new IOException("Dicionário LZMA inválido");
            input=new LZMAInputStream(new ByteArrayInputStream(data,5,data.length-5),expected,data[0],(int)dict);
        }else throw new IOException("Compressão desconhecida: "+kind);
        try(InputStream in=input;ByteArrayOutputStream out=new ByteArrayOutputStream(Math.min(expected,1<<20))) {
            byte[] buf=new byte[65536];int size;int total=0;
            while((size=in.read(buf))!=-1){total+=size;if(total>expected)throw new IOException("Descompactação excedeu limite");out.write(buf,0,size);}
            if(total!=expected)throw new IOException("Comprimento descompactado divergente: "+total+" / "+expected);
            return out.toByteArray();
        }
    }

    static int[] checkMesh(byte[] data) throws IOException {
        if(data.length<12)throw new IOException("Malha curta");
        ByteBuffer b=ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);
        long vertices=Integer.toUnsignedLong(b.getInt(0));
        if(vertices<1||vertices>65536)throw new IOException("Quantidade de vértices inválida");
        long offset=4L+16L*vertices;
        if(offset+4>data.length)throw new IOException("Tabela de vértices truncada");
        long count=Integer.toUnsignedLong(b.getInt((int)offset));
        if(count>4_000_000||count%3!=0||offset+4+2*count>data.length)throw new IOException("Índices triangulares inválidos");
        for(int i=0;i<vertices;i++){
            int pos=4+i*16;
            for(int a=0;a<4;a++){
                float val=b.getFloat(pos+4*a);
                if(!Float.isFinite(val)||Math.abs(val)>1e7)throw new IOException("Coordenada inválida");
                if(a==3&&val!=0f)throw new IOException("Layout XYZW não reconhecido");
            }
        }
        for(int i=0;i<count;i++){
            int idx=Short.toUnsignedInt(b.getShort((int)(offset+4+2L*i)));
            if(idx>=vertices)throw new IOException("Índice fora da malha");
        }
        return new int[]{(int)vertices,(int)count/3};
    }

    private static String gzipBase64(byte[] bytes) throws IOException {
        ByteArrayOutputStream out=new ByteArrayOutputStream();
        try(GZIPOutputStream gz=new GZIPOutputStream(out)){gz.write(bytes);}
        return Base64.encodeToString(out.toByteArray(),Base64.NO_WRAP);
    }
    private static void copyLimited(InputStream in,OutputStream out,long limit) throws IOException {
        byte[] buf=new byte[65536];int r;long n=0;
        while((r=in.read(buf))!=-1){n+=r;if(n>limit)throw new IOException("Arquivo muito grande");out.write(buf,0,r);}
    }
}