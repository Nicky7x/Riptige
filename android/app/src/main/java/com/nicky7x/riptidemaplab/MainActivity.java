package com.nicky7x.riptidemaplab;

import android.app.Activity;
import android.content.*;
import android.graphics.Color;
import android.net.Uri;
import android.os.*;
import android.provider.OpenableColumns;
import android.view.*;
import android.webkit.*;
import android.widget.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Native Android shell for the existing offline 3D editor. */
public final class MainActivity extends Activity {
    private static final int REQUEST_XAPK=1001,REQUEST_EXPORT=1002;
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private WebView web;
    private TextView status;
    private Button importButton,homeButton;
    private String pendingExport="";
    private String pendingName="riptide-arenas-patch.json";
    private final String HTML_TEMPLATE="editor_template.html";

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        getWindow().setStatusBarColor(Color.rgb(12,19,32));
        getWindow().setNavigationBarColor(Color.rgb(12,19,32));
        buildLayout();
        showEditorIfReady();
    }

    private void buildLayout(){
        LinearLayout page=new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setBackgroundColor(Color.rgb(11,18,32));
        // Android 15+ draws behind status/navigation bars with targetSdk 35.
        // Reserve the real system insets so top controls cannot hide under notifications.
        if(Build.VERSION.SDK_INT>=30) {
            getWindow().setDecorFitsSystemWindows(false);
            page.setOnApplyWindowInsetsListener((view,insets)->{
                android.graphics.Insets bars=insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
                view.setPadding(bars.left,Math.max(bars.top,dp(64)),bars.right,bars.bottom);
                return insets;
            });
        } else {
            page.setFitsSystemWindows(true);
            page.setPadding(0,dp(48),0,0);
        }
        LinearLayout toolbar=new LinearLayout(this);
        toolbar.setOrientation(LinearLayout.HORIZONTAL);
        toolbar.setGravity(Gravity.CENTER);
        toolbar.setPadding(dp(18),dp(22),dp(18),dp(18));
        importButton=new Button(this);importButton.setText("Importar XAPK");importButton.setTextSize(13);
        importButton.setAllCaps(false);
        importButton.setOnClickListener(v->selectXapk());
        LinearLayout.LayoutParams left=new LinearLayout.LayoutParams(0,dp(58),1f);
        left.setMargins(dp(4),0,dp(6),0);
        toolbar.addView(importButton,left);
        homeButton=new Button(this);homeButton.setText("Abrir editor");homeButton.setTextSize(13);
        homeButton.setAllCaps(false);
        homeButton.setOnClickListener(v->showEditorIfReady());
        LinearLayout.LayoutParams right=new LinearLayout.LayoutParams(0,dp(52),1f);
        right.setMargins(dp(6),0,dp(4),0);
        toolbar.addView(homeButton,right);
        page.addView(toolbar,new LinearLayout.LayoutParams(-1,-2));
        status=new TextView(this);status.setTextColor(0xffbed8df);status.setTextSize(12);status.setPadding(18,0,18,9);
        page.addView(status,new LinearLayout.LayoutParams(-1,-2));
        web=new WebView(this);WebSettings settings=web.getSettings();
        settings.setJavaScriptEnabled(true);settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);settings.setAllowContentAccess(false);
        settings.setAllowFileAccessFromFileURLs(false);settings.setAllowUniversalAccessFromFileURLs(false);
        settings.setBlockNetworkLoads(false); // All network requests are intercepted and denied, except local JSON.
        web.setBackgroundColor(Color.rgb(11,18,32));
        web.addJavascriptInterface(new Bridge(),"AndroidBridge");
        web.setWebChromeClient(new WebChromeClient(){
            @Override public boolean onConsoleMessage(ConsoleMessage message){
                if(message.messageLevel()==ConsoleMessage.MessageLevel.ERROR)
                    onUi(()->setStatus("Erro 3D: "+message.message()));
                return true;
            }
        });
        web.setWebViewClient(new WebViewClient(){
            @Override public WebResourceResponse shouldInterceptRequest(WebView view,WebResourceRequest request){
                Uri u=request.getUrl();
                if("https".equals(u.getScheme())&&"appassets.androidplatform.net".equals(u.getHost())&&
                    "/arenas_bundle.json".equals(u.getPath())){
                    try{
                        File local=new File(getFilesDir(),"arenas_bundle.json");
                        if(!local.isFile())throw new FileNotFoundException("Arenas não importadas");
                        WebResourceResponse response=new WebResourceResponse("application/json","UTF-8",
                            new BufferedInputStream(new FileInputStream(local)));
                        java.util.Map<String,String> headers=new java.util.HashMap<>();
                        headers.put("Cache-Control","no-store");
                        headers.put("Access-Control-Allow-Origin","*");
                        response.setResponseHeaders(headers);
                        return response;
                    }catch(IOException ignored){
                        return new WebResourceResponse("text/plain","UTF-8",404,"Not Found",
                            java.util.Collections.emptyMap(),new ByteArrayInputStream(new byte[0]));
                    }
                }
                return new WebResourceResponse("text/plain","UTF-8",403,"Forbidden",
                    java.util.Collections.emptyMap(),new ByteArrayInputStream(new byte[0]));
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view,WebResourceRequest request){
                // Our editor contains no external resources. Block all navigations outside itself.
                return !"https".equals(request.getUrl().getScheme()) ||
                    !"appassets.androidplatform.net".equals(request.getUrl().getHost());
            }
        });
        page.addView(web,new LinearLayout.LayoutParams(-1,0,1));setContentView(page);
    }

    private int dp(float size) {
        return Math.round(size*getResources().getDisplayMetrics().density);
    }

    private void selectXapk() {
        Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);intent.setType("*/*");
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        startActivityForResult(intent,REQUEST_XAPK);
    }

    @Override protected void onActivityResult(int req,int result,Intent data){
        super.onActivityResult(req,result,data);
        if(result!=RESULT_OK||data==null||data.getData()==null)return;
        if(req==REQUEST_XAPK)importXapk(data.getData());
        else if(req==REQUEST_EXPORT) {
            String export=pendingExport;pendingExport="";
            worker.execute(()->{
                try(OutputStream output=getContentResolver().openOutputStream(data.getData())){
                    if(output==null)throw new IOException("Não foi possível criar arquivo");
                    output.write(export.getBytes(StandardCharsets.UTF_8));
                    onUi(()->setStatus("Patch salvo com sucesso."));
                }catch(Exception e){onUi(()->setStatus("Erro ao salvar: "+e.getMessage()));}
            });
        }
    }

    private void importXapk(Uri uri){
        importButton.setEnabled(false);setStatus("Importando XAPK… pode levar um pouco. Não feche o aplicativo.");
        worker.execute(()->{
            File source=new File(getCacheDir(),"riptide-upload-local.xapk");
            File apf=new File(getCacheDir(),"Assets.tmp.apf");
            File output=new File(getFilesDir(),"arenas_bundle.json");
            try{
                try(InputStream input=getContentResolver().openInputStream(uri);
                    OutputStream out=new BufferedOutputStream(new FileOutputStream(source))){
                    if(input==null)throw new IOException("Arquivo inacessível");
                    byte[] buffer=new byte[65536];int read;long total=0;
                    while((read=input.read(buffer))!=-1){total+=read;if(total>400L*1024*1024)throw new IOException("XAPK excede 400MB");out.write(buffer,0,read);}
                }
                onUi(()->setStatus("Lendo recursos das pistas…"));
                ApfImporter.extractAssetArchive(source,apf);
                ApfImporter.Result result=ApfImporter.importApf(apf);
                File temp=new File(getFilesDir(),"arenas_bundle.pending");
                try(FileOutputStream out=new FileOutputStream(temp)){
                    out.write(result.json.getBytes(StandardCharsets.UTF_8));
                }
                if(output.exists()&&!output.delete())throw new IOException("Não consegui substituir biblioteca privada");
                if(!temp.renameTo(output))throw new IOException("Não consegui salvar arenas no aparelho");
                onUi(()->{importButton.setEnabled(true);
                    setStatus(result.arenas+" arenas, "+result.meshes+" malhas; "+result.skipped+" ignoradas. Dados salvos offline.");
                    showEditorIfReady();});
            }catch(Exception e){onUi(()->{importButton.setEnabled(true);setStatus("Falha na importação: "+e.getMessage());});}
            finally{if(source.exists())source.delete();if(apf.exists())apf.delete();}
        });
    }

    private void showEditorIfReady(){
        File bundle=new File(getFilesDir(),"arenas_bundle.json");
        if(!bundle.isFile()){
            setStatus("Primeira execução: toque em Importar XAPK. Tudo é processado offline, uma só vez.");
            web.loadDataWithBaseURL("https://appassets.androidplatform.net/",
                "<!doctype html><meta name='viewport' content='width=device-width,initial-scale=1'>"+
                "<style>body{background:#0b1220;color:#e5f3f1;font:16px system-ui;padding:25px;line-height:1.7}</style>"+
                "<h2>Riptide Map Lab 3D</h2><p>O aplicativo não contém arquivos comerciais do jogo.</p>"+
                "<p>Selecione sua cópia original do XAPK uma vez. As arenas serão extraídas e armazenadas somente neste celular.</p>",
                "text/html","UTF-8",null);return;
        }
        worker.execute(()->{
            try{
                String html=readAsset(HTML_TEMPLATE);
                if(!html.contains("__EMBEDDED_ASSETS__"))throw new IOException("Template incompatível");
                // Keep large arena data on disk. Inject only a tiny marker into the HTML.
                html=html.replace("__EMBEDDED_ASSETS__","{\"__external_bundle\":true}");
                final String result=html;
                onUi(()->{setStatus("Editor 3D · arenas locais · sem upload");
                    web.loadDataWithBaseURL("https://appassets.androidplatform.net/",result,"text/html","UTF-8",null);});
            } catch(Exception e){onUi(()->setStatus("Erro ao abrir editor: "+e.getMessage()));}
        });
    }
    private String readAsset(String name)throws IOException{
        try(InputStream in=getAssets().open(name);ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] buf=new byte[16384];int n;while((n=in.read(buf))!=-1)out.write(buf,0,n);
            return out.toString(StandardCharsets.UTF_8.name());
        }
    }
    private static String readFile(File file)throws IOException{
        try(FileInputStream in=new FileInputStream(file);ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] buf=new byte[16384];int n;while((n=in.read(buf))!=-1)out.write(buf,0,n);
            return out.toString(StandardCharsets.UTF_8.name());
        }
    }
    private void setStatus(String message){status.setText(message);}
    private void onUi(Runnable r){runOnUiThread(r);}
    private final class Bridge {
        @JavascriptInterface public void reportError(String message){
            onUi(()->setStatus(message!=null&&message.length()<500?message:"Falha ao iniciar editor"));
        }
        @JavascriptInterface public void editorReady(int count){
            onUi(()->setStatus("Editor 3D pronto · "+count+" arenas locais · sem upload"));
        }
        @JavascriptInterface public void exportJson(String filename,String contents){
            if(contents==null||contents.length()>12_000_000)return;
            onUi(()->{
                pendingExport=contents;
                pendingName=(filename!=null&&filename.endsWith(".json")?filename:"riptide-arenas-patch.json").replaceAll("[^a-zA-Z0-9._-]","_");
                Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("application/json");intent.putExtra(Intent.EXTRA_TITLE,pendingName);
                startActivityForResult(intent,REQUEST_EXPORT);
            });
        }
    }
    @Override public void onBackPressed(){
        if(web.canGoBack())web.goBack();else super.onBackPressed();
    }
    @Override protected void onDestroy(){web.destroy();worker.shutdownNow();super.onDestroy();}
}