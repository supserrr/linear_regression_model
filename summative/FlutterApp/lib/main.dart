import 'dart:convert';
import 'dart:ui' show ImageFilter;

import 'package:device_price_app/app_theme.dart';
import 'package:flutter/foundation.dart' show TargetPlatform, defaultTargetPlatform;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:glass_kit/glass_kit.dart';
import 'package:http/http.dart' as http;

/// Set at build time: `flutter run --dart-define=API_BASE_URL=http://192.168.1.5:8000`
/// (use your computer's LAN IP on a physical phone).
const String _kApiBaseUrlEnv = String.fromEnvironment('API_BASE_URL');

/// Android emulator: `127.0.0.1` is the emulator itself, not your Mac — use host alias.
String get kApiBaseUrl {
  if (_kApiBaseUrlEnv.isNotEmpty) return _kApiBaseUrlEnv;
  if (defaultTargetPlatform == TargetPlatform.android) {
    return 'http://10.0.2.2:8000';
  }
  return 'http://127.0.0.1:8000';
}

/// Matches `top_brands` in `model_metadata.json` plus "Other" for rare brands.
const List<String> kDeviceBrands = [
  'Others',
  'Samsung',
  'Huawei',
  'LG',
  'Lenovo',
  'ZTE',
  'Xiaomi',
  'Oppo',
  'Asus',
  'Alcatel',
  'Other',
];

void main() {
  runApp(const DevicePriceApp());
}

class DevicePriceApp extends StatelessWidget {
  const DevicePriceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Used price',
      theme: buildAppTheme(),
      home: const PredictionFormPage(),
    );
  }
}

class PredictionFormPage extends StatefulWidget {
  const PredictionFormPage({super.key});

  @override
  State<PredictionFormPage> createState() => _PredictionFormPageState();
}

class _PredictionFormPageState extends State<PredictionFormPage> {
  final _formKey = GlobalKey<FormState>();

  String _deviceBrand = kDeviceBrands[1];
  String _os = 'Android';
  String _fourG = 'yes';
  String _fiveG = 'no';

  final _screenSize = TextEditingController(text: '16.5');
  final _rearCam = TextEditingController(text: '48');
  final _frontCam = TextEditingController(text: '16');
  final _internalMem = TextEditingController(text: '128');
  final _ram = TextEditingController(text: '6');
  final _battery = TextEditingController(text: '4000');
  final _weight = TextEditingController(text: '190');
  final _releaseYear = TextEditingController(text: '2021');
  final _daysUsed = TextEditingController(text: '365');
  final _newPrice = TextEditingController(text: '5.2');

  bool _loading = false;
  double? _predictedPrice;
  String? _errorText;

  @override
  void dispose() {
    _screenSize.dispose();
    _rearCam.dispose();
    _frontCam.dispose();
    _internalMem.dispose();
    _ram.dispose();
    _battery.dispose();
    _weight.dispose();
    _releaseYear.dispose();
    _daysUsed.dispose();
    _newPrice.dispose();
    super.dispose();
  }

  void _showSnack(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        behavior: SnackBarBehavior.floating,
        content: Text(message),
      ),
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _loading = true;
      _predictedPrice = null;
      _errorText = null;
    });

    final uri = Uri.parse('$kApiBaseUrl/predict');
    final body = <String, dynamic>{
      'device_brand': _deviceBrand,
      'os': _os,
      '4g': _fourG,
      '5g': _fiveG,
      'screen_size': double.parse(_screenSize.text.trim()),
      'rear_camera_mp': double.parse(_rearCam.text.trim()),
      'front_camera_mp': double.parse(_frontCam.text.trim()),
      'internal_memory': double.parse(_internalMem.text.trim()),
      'ram': double.parse(_ram.text.trim()),
      'battery': double.parse(_battery.text.trim()),
      'weight': double.parse(_weight.text.trim()),
      'release_year': int.parse(_releaseYear.text.trim()),
      'days_used': int.parse(_daysUsed.text.trim()),
      'normalized_new_price': double.parse(_newPrice.text.trim()),
    };

    try {
      final res = await http
          .post(
            uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 30));

      if (!mounted) return;

      if (res.statusCode == 200) {
        final map = jsonDecode(res.body) as Map<String, dynamic>;
        final raw = map['normalized_used_price'];
        final price = raw is num ? raw.toDouble() : double.tryParse('$raw');
        setState(() {
          _predictedPrice = price;
          _errorText = null;
        });
      } else {
        final msg = 'Server returned ${res.statusCode}';
        setState(() {
          _errorText = res.body.isNotEmpty ? res.body : msg;
          _predictedPrice = null;
        });
        _showSnack(msg);
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _errorText = e.toString();
        _predictedPrice = null;
      });
      _showSnack('Could not reach the API. Check the server and URL.');
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final cs = theme.colorScheme;
    final panelW = (MediaQuery.sizeOf(context).width - 40).clamp(120.0, 2000.0);

    return Scaffold(
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              Color(0x1A05A9F4),
              AppPalette.surface,
            ],
            stops: [0.0, 0.28],
          ),
        ),
        child: CustomScrollView(
          slivers: [
            SliverAppBar.large(
              title: const Text('Used price'),
              backgroundColor: Colors.transparent,
            ),
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 8),
              sliver: SliverToBoxAdapter(
                child: Text(
                  'Estimate normalized resale from your device specs.',
                  style: theme.textTheme.bodyLarge?.copyWith(
                    color: cs.onSurfaceVariant,
                    height: 1.35,
                  ),
                ),
              ),
            ),
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
              sliver: SliverToBoxAdapter(
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      _sectionCard(
                        context,
                        panelW,
                        title: 'Device',
                        icon: Icons.smartphone_rounded,
                        children: [
                          DropdownButtonFormField<String>(
                            // ignore: deprecated_member_use
                            value: _deviceBrand,
                            decoration: const InputDecoration(
                              labelText: 'Brand',
                              prefixIcon: Icon(Icons.branding_watermark_outlined),
                            ),
                            items: kDeviceBrands
                                .map(
                                  (b) => DropdownMenuItem(
                                    value: b,
                                    child: Text(b),
                                  ),
                                )
                                .toList(),
                            onChanged: (v) =>
                                setState(() => _deviceBrand = v!),
                          ),
                          const SizedBox(height: 14),
                          DropdownButtonFormField<String>(
                            // ignore: deprecated_member_use
                            value: _os,
                            decoration: const InputDecoration(
                              labelText: 'Operating system',
                              prefixIcon: Icon(Icons.layers_outlined),
                            ),
                            items: const [
                              DropdownMenuItem(
                                value: 'Android',
                                child: Text('Android'),
                              ),
                              DropdownMenuItem(
                                value: 'iOS',
                                child: Text('iOS'),
                              ),
                            ],
                            onChanged: (v) => setState(() => _os = v!),
                          ),
                          const SizedBox(height: 14),
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Expanded(
                                child: DropdownButtonFormField<String>(
                                  // ignore: deprecated_member_use
                                  value: _fourG,
                                  decoration: const InputDecoration(
                                    labelText: '4G',
                                    prefixIcon: Icon(Icons.signal_cellular_alt),
                                  ),
                                  items: const [
                                    DropdownMenuItem(
                                      value: 'yes',
                                      child: Text('Yes'),
                                    ),
                                    DropdownMenuItem(
                                      value: 'no',
                                      child: Text('No'),
                                    ),
                                  ],
                                  onChanged: (v) =>
                                      setState(() => _fourG = v!),
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: DropdownButtonFormField<String>(
                                  // ignore: deprecated_member_use
                                  value: _fiveG,
                                  decoration: const InputDecoration(
                                    labelText: '5G',
                                    prefixIcon:
                                        Icon(Icons.signal_cellular_alt_2_bar),
                                  ),
                                  items: const [
                                    DropdownMenuItem(
                                      value: 'yes',
                                      child: Text('Yes'),
                                    ),
                                    DropdownMenuItem(
                                      value: 'no',
                                      child: Text('No'),
                                    ),
                                  ],
                                  onChanged: (v) =>
                                      setState(() => _fiveG = v!),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                      _sectionCard(
                        context,
                        panelW,
                        title: 'Hardware',
                        icon: Icons.memory_outlined,
                        children: [
                          _numField(
                            _screenSize,
                            'Screen size',
                            icon: Icons.aspect_ratio,
                          ),
                          _numField(
                            _rearCam,
                            'Rear camera (MP)',
                            icon: Icons.camera_rear_outlined,
                          ),
                          _numField(
                            _frontCam,
                            'Front camera (MP)',
                            icon: Icons.camera_front_outlined,
                          ),
                          _numField(
                            _internalMem,
                            'Internal memory (GB)',
                            icon: Icons.sd_storage_outlined,
                          ),
                          _numField(
                            _ram,
                            'RAM (GB)',
                            icon: Icons.speed_outlined,
                          ),
                          _numField(
                            _battery,
                            'Battery (mAh)',
                            icon: Icons.battery_charging_full_outlined,
                          ),
                          _numField(
                            _weight,
                            'Weight (g)',
                            icon: Icons.scale_outlined,
                          ),
                        ],
                      ),
                      _sectionCard(
                        context,
                        panelW,
                        title: 'Usage & market',
                        icon: Icons.trending_up_outlined,
                        children: [
                          _intField(
                            _releaseYear,
                            'Release year',
                            icon: Icons.calendar_today_outlined,
                          ),
                          _intField(
                            _daysUsed,
                            'Days used',
                            icon: Icons.schedule_outlined,
                          ),
                          _numField(
                            _newPrice,
                            'Normalized new price',
                            icon: Icons.price_change_outlined,
                            helperText:
                                'Same scale as in the training dataset (log-normalized new price).',
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      FilledButton.icon(
                        onPressed: _loading ? null : _submit,
                        icon: _loading
                            ? SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Icon(Icons.analytics_outlined),
                        label: Text(
                          _loading ? 'Working…' : 'Estimate price',
                        ),
                      ),
                      const SizedBox(height: 24),
                      AnimatedSwitcher(
                        duration: const Duration(milliseconds: 320),
                        switchInCurve: Curves.easeOutCubic,
                        switchOutCurve: Curves.easeInCubic,
                        child: _predictedPrice != null
                            ? _ResultCard(
                                key: ValueKey(_predictedPrice),
                                width: panelW,
                                price: _predictedPrice!,
                              )
                            : const SizedBox.shrink(),
                      ),
                      if (_errorText != null) ...[
                        const SizedBox(height: 16),
                        _ErrorBanner(message: _errorText!),
                      ],
                      const SizedBox(height: 20),
                      _FrostedPanel(
                        width: panelW,
                        margin: EdgeInsets.zero,
                        blurSigma: 14,
                        child: Theme(
                          data: theme.copyWith(dividerColor: Colors.transparent),
                          child: ExpansionTile(
                            leading: Icon(
                              Icons.link_rounded,
                              color: cs.primary,
                            ),
                            title: Text(
                              'API connection',
                              style: theme.textTheme.titleSmall,
                            ),
                            subtitle: Text(
                              'Advanced',
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: cs.onSurfaceVariant,
                              ),
                            ),
                            children: [
                              Padding(
                                padding: const EdgeInsets.fromLTRB(
                                  16,
                                  0,
                                  16,
                                  16,
                                ),
                                child: SelectableText(
                                  kApiBaseUrl,
                                  style: theme.textTheme.bodySmall?.copyWith(
                                    fontFamily: 'monospace',
                                    color: cs.onSurfaceVariant,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _sectionCard(
    BuildContext context,
    double panelW, {
    required String title,
    required IconData icon,
    required List<Widget> children,
  }) {
    final theme = Theme.of(context);
    final cs = theme.colorScheme;

    return _FrostedPanel(
      width: panelW,
      margin: const EdgeInsets.only(bottom: 16),
      blurSigma: 16,
      padding: const EdgeInsets.fromLTRB(16, 18, 16, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Icon(icon, size: 22, color: cs.primary),
              const SizedBox(width: 10),
              Text(
                title,
                style: theme.textTheme.titleMedium,
              ),
            ],
          ),
          const SizedBox(height: 16),
          ...children,
        ],
      ),
    );
  }

  Widget _numField(
    TextEditingController c,
    String label, {
    IconData? icon,
    String? helperText,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        controller: c,
        keyboardType: const TextInputType.numberWithOptions(decimal: true),
        inputFormatters: [
          FilteringTextInputFormatter.allow(RegExp(r'[0-9.]')),
        ],
        decoration: InputDecoration(
          labelText: label,
          helperText: helperText,
          prefixIcon: icon != null ? Icon(icon, size: 22) : null,
        ),
        validator: (s) {
          if (s == null || s.trim().isEmpty) return 'Required';
          if (double.tryParse(s.trim()) == null) return 'Enter a number';
          return null;
        },
      ),
    );
  }

  Widget _intField(
    TextEditingController c,
    String label, {
    IconData? icon,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        controller: c,
        keyboardType: TextInputType.number,
        inputFormatters: [FilteringTextInputFormatter.digitsOnly],
        decoration: InputDecoration(
          labelText: label,
          prefixIcon: icon != null ? Icon(icon, size: 22) : null,
        ),
        validator: (s) {
          if (s == null || s.trim().isEmpty) return 'Required';
          if (int.tryParse(s.trim()) == null) return 'Enter an integer';
          return null;
        },
      ),
    );
  }
}

class _ResultCard extends StatelessWidget {
  const _ResultCard({
    super.key,
    required this.width,
    required this.price,
  });

  final double width;
  final double price;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final cs = theme.colorScheme;

    return GlassContainer.frostedGlass(
      width: width,
      height: 168,
      borderRadius: BorderRadius.circular(18),
      blur: 18,
      frostedOpacity: 0.16,
      borderWidth: 1.4,
      borderColor: AppPalette.blue.withValues(alpha: 0.4),
      borderGradient: LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [
          AppPalette.blue.withValues(alpha: 0.65),
          AppPalette.blue.withValues(alpha: 0.12),
        ],
      ),
      padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 20),
      alignment: Alignment.topLeft,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Icon(Icons.check_circle_outline_rounded, color: cs.primary),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Estimated normalized used price',
                  style: theme.textTheme.titleSmall?.copyWith(
                    color: AppPalette.ink,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            price.toStringAsFixed(4),
            style: theme.textTheme.headlineMedium?.copyWith(
              fontWeight: FontWeight.w700,
              letterSpacing: -0.5,
              color: AppPalette.ink,
              fontFeatures: const [FontFeature.tabularFigures()],
            ),
          ),
        ],
      ),
    );
  }
}

/// Intrinsic-height frosted panel for scroll columns. [GlassContainer] from
/// glass_kit uses expanded sizing and requires a fixed height; form sections use
/// this [BackdropFilter] panel instead for the same glass look.
class _FrostedPanel extends StatelessWidget {
  const _FrostedPanel({
    required this.width,
    required this.child,
    this.margin,
    this.padding,
    this.blurSigma = 14,
  });

  final double width;
  final Widget child;
  final EdgeInsetsGeometry? margin;
  final EdgeInsetsGeometry? padding;
  final double blurSigma;

  @override
  Widget build(BuildContext context) {
    final r = BorderRadius.circular(18);

    return Container(
      width: width,
      margin: margin,
      child: ClipRRect(
        borderRadius: r,
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: blurSigma, sigmaY: blurSigma),
          child: Container(
            padding: padding,
            decoration: BoxDecoration(
              borderRadius: r,
              border: Border.all(
                width: 1.2,
                color: AppPalette.blue.withValues(alpha: 0.28),
              ),
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  Colors.white.withValues(alpha: 0.62),
                  Colors.white.withValues(alpha: 0.28),
                ],
              ),
            ),
            child: child,
          ),
        ),
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final cs = theme.colorScheme;

    return Material(
      color: cs.errorContainer,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.error_outline_rounded, color: cs.error),
            const SizedBox(width: 10),
            Expanded(
              child: SelectableText(
                message,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: cs.onErrorContainer,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
