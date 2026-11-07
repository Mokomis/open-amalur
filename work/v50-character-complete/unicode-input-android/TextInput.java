package org.opemamalur.scene;

import android.app.Activity;
import android.text.Editable;
import android.text.InputFilter;
import android.text.Spanned;
import android.text.TextWatcher;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.InputMethodManager;
import android.widget.EditText;
import java.util.HashMap;

/** Invisible text transport. All visible name controls remain in Veil. */
public final class TextInput {
    private static native void changed(long token, String value, int confirmed, long revision);
    private static final HashMap<Long, Editor> editors = new HashMap<>();
    private static final class Editor {
        final Activity activity;
        final long token;
        EditText field;
        long revision;
        boolean closed, synchronizing;
        Editor(Activity a, long t) { activity = a; token = t; }
        String value() { return field.getText().toString(); }
        void finish(int result) {
            if (closed) return;
            String text = value();
            changed(token, text, result, ++revision);
            dispose();
        }
        void dispose() {
            if (closed) return;
            closed = true;
            InputMethodManager imm = (InputMethodManager) activity.getSystemService(Activity.INPUT_METHOD_SERVICE);
            if (imm != null) imm.hideSoftInputFromWindow(field.getWindowToken(), 0);
            field.clearFocus();
            if (field.getParent() instanceof ViewGroup) ((ViewGroup) field.getParent()).removeView(field);
            editors.remove(token);
        }
    }
    private static boolean accepted(String text) {
        int count = 0;
        for (int at = 0; at < text.length();) {
            char c = text.charAt(at);
            if (Character.isLowSurrogate(c)) return false;
            if (Character.isHighSurrogate(c) && (at + 1 == text.length() || !Character.isLowSurrogate(text.charAt(at + 1)))) return false;
            int cp = Character.codePointAt(text, at);
            if (cp < 32 || cp == 127 || ++count > 16) return false;
            at += Character.charCount(cp);
        }
        return true;
    }
    public static void open(final Activity activity, final long token, final String initial) {
        activity.runOnUiThread(() -> {
            if (activity.isFinishing() || activity.isDestroyed()) return;
            Editor previous = editors.get(token);
            if (previous != null) previous.dispose();
            final Editor e = new Editor(activity, token);
            final EditText field = new EditText(activity);
            e.field = field;
            field.setSingleLine(true);
            field.setInputType(android.text.InputType.TYPE_CLASS_TEXT | android.text.InputType.TYPE_TEXT_VARIATION_PERSON_NAME);
            field.setImeOptions(EditorInfo.IME_ACTION_DONE | EditorInfo.IME_FLAG_NO_EXTRACT_UI);
            field.setAlpha(0f);
            field.setFilters(new InputFilter[]{new InputFilter() {
                @Override public CharSequence filter(CharSequence source, int start, int end, Spanned dest, int dstart, int dend) {
                    String candidate = dest.subSequence(0, dstart).toString() + source.subSequence(start, end) + dest.subSequence(dend, dest.length());
                    return accepted(candidate) ? null : dest.subSequence(dstart, dend);
                }
            }});
            field.setText(initial);
            field.selectAll();
            field.addTextChangedListener(new TextWatcher() {
                public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
                public void onTextChanged(CharSequence s, int start, int before, int count) {}
                public void afterTextChanged(Editable s) {
                    if (!e.closed && !e.synchronizing) changed(token, s.toString(), 0, ++e.revision);
                }
            });
            field.setOnEditorActionListener((v, action, event) -> {
                if (action == EditorInfo.IME_ACTION_DONE || (event != null && event.getKeyCode() == KeyEvent.KEYCODE_ENTER)) { e.finish(1); return true; }
                return false;
            });
            field.setOnKeyListener((v, code, event) -> {
                if ((code == KeyEvent.KEYCODE_ESCAPE || code == KeyEvent.KEYCODE_BUTTON_B) && event.getAction() == KeyEvent.ACTION_UP) { e.finish(-1); return true; }
                return false;
            });
            editors.put(token, e);
            activity.addContentView(field, new ViewGroup.LayoutParams(1, 1));
            field.requestFocus();
            field.post(() -> {
                if (e.closed) return;
                InputMethodManager imm = (InputMethodManager) activity.getSystemService(Activity.INPUT_METHOD_SERVICE);
                if (imm != null) imm.showSoftInput(field, InputMethodManager.SHOW_IMPLICIT);
            });
        });
    }
    public static void sync(final Activity activity, final long token, final String value, final long acknowledgedRevision) {
        activity.runOnUiThread(() -> {
            Editor e = editors.get(token);
            if (e == null || e.closed || e.revision > acknowledgedRevision || e.value().equals(value)) return;
            e.synchronizing = true;
            e.field.setText(value);
            e.field.setSelection(e.field.length());
            e.synchronizing = false;
        });
    }
    public static void hide(final Activity activity, final long token) {
        activity.runOnUiThread(() -> { Editor e = editors.get(token); if (e != null) e.dispose(); });
    }
}
