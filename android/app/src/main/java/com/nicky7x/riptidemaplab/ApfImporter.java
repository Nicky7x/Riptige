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
    private static final String STATIC_PREFIX = "VuStaticModelAsset/Level/";
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
        JSONObject visuals=new JSONObject();
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
                if(name.startsWith(PREFIX) || name.startsWith(STATIC_PREFIX)) {
                    if(usize>MAX_RESOURCE||csize>MAX_RESOURCE){skipped++;continue;}
                    entries.add(new Entry(name,off,(int)usize,(int)csize,flags));
                }
            }
            if(p!=idx.length)throw new IOException("Bytes desconhecidos no índice APF");
            for(Entry e:entries) {
                try {
                    byte[] raw=new byte[e.csize];file.seek(e.offset);file.readFully(raw);
                    byte[] mesh=unpack(raw,e.usize,e.flags);
                    if(e.name.startsWith(STATIC_PREFIX)) {
                        byte[] preview=makeVisualPreview(mesh);
                        String suffix=e.name.substring(STATIC_PREFIX.length());
                        int slash=suffix.indexOf('/');
                        if(slash<1||slash==suffix.length()-1)throw new IOException("Nome de modelo inválido");
                        String arena=suffix.substring(0,slash),model=suffix.substring(slash+1);
                        JSONObject group=visuals.optJSONObject(arena);
                        if(group==null){group=new JSONObject();visuals.put(arena,group);}
                        JSONObject rec=new JSONObject();
                        rec.put("blob",gzipBase64(preview));rec.put("size",preview.length);
                        rec.put("source",e.name);
                        group.put(model,rec);
                        continue;
                    }
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
        int arenaCount=arenas.length();
        arenas.put("__visuals",visuals);
        return new Result(arenas.toString(),arenaCount,meshes,skipped);
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


    /** Strict read-only subset of VuStaticModelAsset. Generates a DISPLAY-ONLY
     * XYZW/u16 shape compatible with the existing WebGL viewer; not a game asset.
     * Vertex positions are the first 3 floats of each interleaved vertex stream.
     * Validated against 223 of 248 Level models in the user's APF by Python parser.
     */
    static byte[] makeVisualPreview(byte[] data) throws IOException {
        ByteBuffer b=ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);
        if(data.length<64)throw new IOException("Modelo visual muito curto");
        for(int i=0;i<3;i++) {
            float lod=b.getFloat(4*i);
            if(!Float.isFinite(lod)||lod<0||lod>1e6)throw new IOException("Cabeçalho visual inesperado");
        }
        int materials=b.getInt(46),p=50;
        if(materials<1||materials>256)throw new IOException("Tabela de materiais inválida");
        for(int m=0;m<materials;m++){
            int end=p;
            while(end<data.length&&end-p<=1024&&data[end]!=0)end++;
            if(end>=data.length||end-p>1024||end==p)throw new IOException("Material sem nome");
            p=end+1;
        }
        if(p+4>data.length)throw new IOException("Tabela visual truncada");
        long groupCount=Integer.toUnsignedLong(b.getInt(p));p+=4;
        if(groupCount>8192||groupCount*48L>data.length-p-8)throw new IOException("Grupos inválidos");
        int[][] groups=new int[(int)groupCount][4];
        for(int i=0;i<groupCount;i++){
            for(int k=0;k<4;k++)groups[i][k]=b.getInt(p+4*k);
            int material=groups[i][1];
            if(material<0||material>=materials)throw new IOException("Referência de material desconhecida");
            for(int k=0;k<3;k++){
                float low=b.getFloat(p+16+4*k),high=b.getFloat(p+32+4*k);
                if(!Float.isFinite(low)||!Float.isFinite(high)||Math.abs(low)>1e7||Math.abs(high)>1e7)
                    throw new IOException("Limites visuais inválidos");
            }
            p+=48;
        }
        if(p+8>data.length)throw new IOException("Streams ausentes");
        int unknown=b.getInt(p),streamCount=b.getInt(p+4);p+=8;
        if(unknown!=0||streamCount<1||streamCount>64)throw new IOException("Cabeçalho de streams não reconhecido");
        ByteArrayOutputStream vtx=new ByteArrayOutputStream(),idx=new ByteArrayOutputStream();
        int[] indicesCount=new int[streamCount];
        int count=0,totalIndices=0;
        for(int stream=0;stream<streamCount;stream++){
            if(p+8>data.length)throw new IOException("Stream truncado");
            int stride=b.getInt(p),length=b.getInt(p+4);p+=8;
            if(stride<12||stride>128||length<0||length%stride!=0||length>data.length-p)
                throw new IOException("Vértices do modelo inválidos");
            int vertices=length/stride;
            if((long)vertices+count>65535)throw new IOException("Modelo excede índices de 16 bits");
            for(int i=0;i<vertices;i++){
                int pos=p+i*stride;
                ByteBuffer vec=ByteBuffer.allocate(16).order(ByteOrder.LITTLE_ENDIAN);
                for(int a=0;a<3;a++){
                    float f=b.getFloat(pos+4*a);
                    if(!Float.isFinite(f)||Math.abs(f)>1e7)throw new IOException("Vértice visual inválido");
                    vec.putFloat(f);
                }
                vec.putFloat(0);
                vtx.write(vec.array(),0,16);
            }
            p+=length;
            if(p+4>data.length)throw new IOException("Índices de modelo ausentes");
            int indices=b.getInt(p);p+=4;
            if(indices<0||indices>900000||indices%3!=0||2L*indices>data.length-p||(long)indices+totalIndices>480000)
                throw new IOException("Índices visuais inválidos");
            for(int i=0;i<indices;i++){
                int index=Short.toUnsignedInt(b.getShort(p+2*i));
                if(index>=vertices)throw new IOException("Referência visual de vértice inválida");
                int output=index+count;
                idx.write(output&255);idx.write((output>>8)&255);
            }
            p+=2*indices;count+=vertices;totalIndices+=indices;indicesCount[stream]=indices;
        }
        if(p+1!=data.length||data[p]!=0)throw new IOException("Rodapé visual ainda não reconhecido");
        for(int[] group:groups){
            int stream=group[0],start=group[2],triangles=group[3];
            if(stream<0||stream>=streamCount||start<0||triangles<0||3L*triangles+start>indicesCount[stream])
                throw new IOException("Grupo visual aponta fora de stream");
        }
        ByteBuffer preview=ByteBuffer.allocate(8+vtx.size()+idx.size()).order(ByteOrder.LITTLE_ENDIAN);
        preview.putInt(count);preview.put(vtx.toByteArray());preview.putInt(totalIndices);preview.put(idx.toByteArray());
        return preview.array();
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