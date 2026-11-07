package org.opemamalur.scene;

import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.graphics.fonts.Font;
import android.graphics.fonts.FontFamily;
import android.graphics.fonts.FontStyle;
import android.os.Build;
import android.text.Layout;
import android.text.StaticLayout;
import android.text.TextDirectionHeuristics;
import android.text.TextPaint;
import java.io.IOException;

/** Whole-string layout/rasterization for non-ASCII Veil text.
 * No Activity is retained. Java pixels stay premultiplied; JNI converts the
 * copied output to straight RGBA and recycles the returned bitmap immediately.
 * JNI-visible names/fields must be retained if a later shrinker is introduced.
 */
public final class TextRasterizer {
    private TextRasterizer() {}
    private static final Typeface[] FONTS = new Typeface[2];

    public static final class Result {
        public final Bitmap bitmap;
        public final float advance, originX, originY;
        private Result(Bitmap bitmap, float advance, float x, float y) {
            this.bitmap = bitmap; this.advance = advance;
            this.originX = x; this.originY = y;
        }
    }

    private static synchronized Typeface font(Activity activity, int which)
            throws IOException {
        Typeface type = FONTS[which];
        if (type == null) {
            final String path = which == 0 ? "fonts/Cinzel.ttf" : "fonts/Alegreya.ttf";
            if (Build.VERSION.SDK_INT >= 29) {
                type = Api29.makeFont(activity, path, which == 0 ? 600 : 500);
            } else {
                // API26-28 framework asset Typeface uses Android's fallback chain.
                // Prefer the source variable font's same wght instance as atlas.
                type = new Typeface.Builder(activity.getApplicationContext().getAssets(), path)
                        .setFontVariationSettings(which == 0 ? "'wght' 600" : "'wght' 500")
                        .build();
            }
            if (type == null) throw new IOException("Missing source UI font: " + path);
            FONTS[which] = type;
        }
        return type;
    }

    private static final class Api29 {
        static Typeface makeFont(Activity activity, String path, int weight)
                throws IOException {
            Font face = new Font.Builder(activity.getApplicationContext().getAssets(), path)
                    .setWeight(weight)
                    .setFontVariationSettings("'wght' " + weight)
                    .build();
            FontFamily family = new FontFamily.Builder(face).build();
            return new Typeface.CustomFallbackBuilder(family)
                    .setSystemFallback("sans-serif")
                    .setStyle(new FontStyle(weight, FontStyle.FONT_SLANT_UPRIGHT))
                    .build();
        }
    }

    private static final class Api35 {
        static RectF ink(StaticLayout layout) { return layout.computeDrawingBoundingBox(); }
    }

    private static boolean valid(String text) {
        if (text == null || text.length() == 0 || text.length() > 512) return false;
        int scalars = 0;
        for (int i = 0; i < text.length();) {
            int cp = text.codePointAt(i);
            if (cp < 32 || cp == 127 || (cp >= 0xd800 && cp <= 0xdfff)
                    || ++scalars > 256) return false;
            i += Character.charCount(cp);
        }
        return true;
    }

    /** Called on an attached native render thread; no View/UI-thread mutation.
     * pixelSize is physical px, not sp/dp. Return null on any unsupported request.
     * A returned bitmap is exclusive, mutable software ARGB_8888 and must be
     * recycled by the JNI caller once its pixels have been copied/unlocked.
     */
    public static Result render(Activity activity, String text, int which, int pixelSize) {
        if (activity == null || which < 0 || which > 1 || pixelSize < 1
                || pixelSize > 256 || !valid(text)) return null;
        Bitmap bitmap = null;
        try {
            TextPaint paint = new TextPaint(Paint.ANTI_ALIAS_FLAG | Paint.SUBPIXEL_TEXT_FLAG);
            paint.setTypeface(font(activity, which));
            paint.setTextSize(pixelSize);
            paint.setColor(Color.WHITE);
            // Entire text, including combining marks/bidi runs, stays in one layout.
            final float advance = Layout.getDesiredWidth(text, paint);
            if (Float.isNaN(advance) || Float.isInfinite(advance)
                    || advance < 0 || advance > 4000) return null;
            final int logicalWidth = Math.max(1, (int)Math.ceil(advance));
            StaticLayout.Builder builder = StaticLayout.Builder.obtain(text, 0,
                    text.length(), paint, logicalWidth)
                    .setAlignment(Layout.Alignment.ALIGN_NORMAL)
                    .setTextDirection(TextDirectionHeuristics.FIRSTSTRONG_LTR)
                    .setIncludePad(false).setLineSpacing(0, 1)
                    .setBreakStrategy(Layout.BREAK_STRATEGY_SIMPLE)
                    .setHyphenationFrequency(Layout.HYPHENATION_FREQUENCY_NONE);
            if (Build.VERSION.SDK_INT >= 28) builder.setUseLineSpacingFromFallbacks(true);
            final StaticLayout layout = builder.build();

            float left = 0, top = 0, right = logicalWidth, bottom = layout.getHeight();
            if (Build.VERSION.SDK_INT >= 35) {
                // Actual shaped/fallback glyph ink bounds preserve tall marks/overhang.
                RectF ink = Api35.ink(layout);
                if (ink != null) {
                    left = Math.min(left, ink.left); top = Math.min(top, ink.top);
                    right = Math.max(right, ink.right); bottom = Math.max(bottom, ink.bottom);
                }
            } else {
                // Older APIs lack shaped-layout ink bounds. Include whole-text
                // Paint bounds plus half-em guard; no universal-overhang claim.
                Rect ink = new Rect();
                paint.getTextBounds(text, 0, text.length(), ink);
                int baseline = layout.getLineBaseline(0);
                left = Math.min(left, ink.left); top = Math.min(top, baseline + ink.top);
                right = Math.max(right, ink.right); bottom = Math.max(bottom, baseline + ink.bottom);
            }
            final int padding = Build.VERSION.SDK_INT >= 35 ? 3 : pixelSize / 2 + 4;
            final float originX = (float)Math.floor(left) - padding;
            final float originY = (float)Math.floor(top) - padding;
            final int width = (int)Math.ceil(right) + padding - (int)originX;
            final int height = (int)Math.ceil(bottom) + padding - (int)originY;
            if (Float.isNaN(originX) || Float.isNaN(originY) || width < 1 || height < 1
                    || width > 4096 || height > 4096 || (long)width * height > 1048576L
                    || Math.abs(originX) > 4096 || Math.abs(originY) > 4096) return null;
            bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
            bitmap.eraseColor(Color.TRANSPARENT);
            Canvas canvas = new Canvas(bitmap);
            canvas.translate(-originX, -originY);
            layout.draw(canvas);
            return new Result(bitmap, advance, originX, originY);
        } catch (IOException | RuntimeException | OutOfMemoryError unavailable) {
            if (bitmap != null) bitmap.recycle();
            return null;
        }
    }
}
