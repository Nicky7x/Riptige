package com.nicky7x.riptidemaplab;

import org.junit.Test;
import static org.junit.Assert.*;

public class WebRequestPolicyTest {
    @Test public void webviewMustHandleInternalHtmlDataUris() {
        assertTrue(WebRequestPolicy.browserHandled("data"));
        assertTrue(WebRequestPolicy.browserHandled("about"));
        assertTrue(WebRequestPolicy.browserHandled("blob"));
        assertFalse(WebRequestPolicy.browserHandled("http"));
        assertFalse(WebRequestPolicy.browserHandled("https"));
        assertFalse(WebRequestPolicy.browserHandled("file"));
    }

    @Test public void onlyLocalImportedCatalogMayBeServed() {
        assertTrue(WebRequestPolicy.isLocalLibrary("https","appassets.androidplatform.net","/arenas_bundle.json"));
        assertFalse(WebRequestPolicy.isLocalLibrary("http","appassets.androidplatform.net","/arenas_bundle.json"));
        assertFalse(WebRequestPolicy.isLocalLibrary("https","other.example","/arenas_bundle.json"));
        assertFalse(WebRequestPolicy.isLocalLibrary("https","appassets.androidplatform.net","/internet"));
    }
}
