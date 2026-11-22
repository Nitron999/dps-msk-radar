import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

const String supabaseUrl = 'https://mobpdvfwfwpxbxehlumm.supabase.co';
const String supabaseAnonKey = 'sb_publishable_Ru7JMBz4-GVNCyjiTrDrwQ_kkACosiz';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Supabase.initialize(
    url: supabaseUrl,
    anonKey: supabaseAnonKey,
  );
  runApp(const DpsMonitorApp());
}

class DpsMonitorApp extends StatelessWidget {
  const DpsMonitorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'ДПС — Москва и МО',
      theme: ThemeData.dark(useMaterial3: true),
      home: const MapScreen(),
    );
  }
}

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  final MapController _mapController = MapController();
  final _supabase = Supabase.instance.client;

  final LatLngBounds _moscowRegionBounds = LatLngBounds(
    const LatLng(54.2, 35.1),
    const LatLng(56.9, 40.2),
  );

  late final Stream<List>> _marksStream;

  @override
  void initState() {
    super.initState();
    _marksStream = _supabase
        .from('patrol_marks')
        .stream(primaryKey: ['id'])
        .order('created_at', ascending: false);
  }

  Future<void> _sendMarkToCloud(LatLng point, String comment) async {
    await _supabase.from('patrol_marks').insert({
      'lat': point.latitude,
      'lng': point.longitude,
      'type': 'dps',
      'comment': comment.isEmpty ? 'Экипаж ДПС' : comment,
    });
  }

  void _showAddDialog(LatLng point) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Отметить экипаж ДПС'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(
            hintText: 'Например: МКАД 45 км, внешнее',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Отмена'),
          ),
          FilledButton(
            onPressed: () async {
              Navigator.pop(ctx);
              await _sendMarkToCloud(point, controller.text.trim());
            },
            child: const Text('Отправить'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ДПС: Москва и МО'),
        actions: [
          IconButton(
            icon: const Icon(Icons.my_location),
            tooltip: 'Центр Москвы',
            onPressed: () =>
                _mapController.move(const LatLng(55.7558, 37.6173), 10),
          ),
        ],
      ),
      body: StreamBuilder<List>>(
        stream: _marksStream,
        builder: (context, snapshot) {
          final now = DateTime.now().toUtc();
          final rawMarks = snapshot.data ?? [];

          final activeMarks = rawMarks.where((m) {
            final created = DateTime.parse(m['created_at']);
            return now.difference(created).inMinutes < 60;
          }).toList();

          return FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: const LatLng(55.7558, 37.6173),
              initialZoom: 10.0,
              minZoom: 8.0,
              maxZoom: 18.0,
              cameraConstraint:
                  CameraConstraint.contain(bounds: _moscowRegionBounds),
              onLongPress: (_, latLng) => _showAddDialog(latLng),
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.dps.msk_radar',
              ),
              MarkerLayer(
                markers: activeMarks.map((mark) {
                  return Marker(
                    point: LatLng(
                      (mark['lat'] as num).toDouble(),
                      (mark['lng'] as num).toDouble(),
                    ),
                    width: 48,
                    height: 48,
                    child: GestureDetector(
                      onTap: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text(mark['comment'] ?? 'Экипаж ДПС'),
                            duration: const Duration(seconds: 3),
                          ),
                        );
                      },
                      child: const Icon(
                        Icons.local_police,
                        color: Colors.blueAccent,
                        size: 38,
                      ),
                    ),
                  );
                }).toList(),
              ),
            ],
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showAddDialog(_mapController.camera.center),
        icon: const Icon(Icons.add_location_alt),
        label: const Text('Поставить метку ДПС'),
      ),
    );
  }
}
