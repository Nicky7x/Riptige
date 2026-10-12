package com.nicky7x.riptidemaplab;

/** Restrictive offline WebView policy; internal document schemes are not HTTP resources. */
final class WebRequestPolicy {
    private WebRequestPolicy() {}
    static boolean browserHandled(String scheme) {
        return "data".equals(scheme) || "about".equals(scheme) || "blob".equals(scheme);
    }
    static boolean isLocalLibrary(String scheme,String host,String path) {
        return "https".equals(scheme) &&
            "appassets.androidplatform.net".equals(host) &&
            "/arenas_bundle.json".equals(path);
    }
}
