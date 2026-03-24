import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Brand palette: blue `#05a9f4`, surface `#F4F4F4`, ink `#171717`, muted `#616161`.
abstract final class AppPalette {
  static const Color blue = Color(0xFF05A9F4);
  static const Color surface = Color(0xFFF4F4F4);
  static const Color ink = Color(0xFF171717);
  static const Color muted = Color(0xFF616161);
}

/// Space Grotesk typography + light scheme aligned to the brand palette.
ThemeData buildAppTheme() {
  const primary = AppPalette.blue;
  const surface = AppPalette.surface;
  const onSurface = AppPalette.ink;
  const onSurfaceVariant = AppPalette.muted;

  final colorScheme = ColorScheme.light(
    primary: primary,
    onPrimary: Colors.white,
    primaryContainer: Color(0xFFD6EEFB),
    onPrimaryContainer: onSurface,
    secondary: primary,
    onSecondary: Colors.white,
    surface: surface,
    onSurface: onSurface,
    onSurfaceVariant: onSurfaceVariant,
    error: Color(0xFFB3261E),
    onError: Colors.white,
    errorContainer: Color(0xFFF9DEDC),
    onErrorContainer: Color(0xFF410E0B),
    outline: onSurfaceVariant.withValues(alpha: 0.45),
    surfaceContainerHighest: Colors.white.withValues(alpha: 0.88),
  );

  final base = ThemeData(
    useMaterial3: true,
    colorScheme: colorScheme,
    scaffoldBackgroundColor: surface,
    appBarTheme: AppBarTheme(
      backgroundColor: Colors.transparent,
      foregroundColor: onSurface,
      elevation: 0,
      scrolledUnderElevation: 0,
    ),
    cardTheme: CardThemeData(
      elevation: 0,
      color: Colors.transparent,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      clipBehavior: Clip.antiAlias,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white.withValues(alpha: 0.82),
      labelStyle: TextStyle(color: onSurfaceVariant),
      floatingLabelStyle: TextStyle(color: primary),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(
          color: onSurfaceVariant.withValues(alpha: 0.35),
        ),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: primary, width: 2),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: colorScheme.error),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: primary,
        foregroundColor: Colors.white,
        disabledBackgroundColor: onSurfaceVariant.withValues(alpha: 0.35),
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        elevation: 0,
      ),
    ),
  );

  final sg = GoogleFonts.spaceGroteskTextTheme(base.textTheme);
  return base.copyWith(
    textTheme: sg.apply(
      bodyColor: onSurface,
      displayColor: onSurface,
    ).copyWith(
      titleLarge: sg.titleLarge?.copyWith(fontWeight: FontWeight.w600),
      titleMedium: sg.titleMedium?.copyWith(fontWeight: FontWeight.w600),
      titleSmall: sg.titleSmall?.copyWith(fontWeight: FontWeight.w600),
      headlineMedium: sg.headlineMedium?.copyWith(fontWeight: FontWeight.w700),
    ),
  );
}
