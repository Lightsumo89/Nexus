import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import { useEffect } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { Court } from "../types";

type CourtMapProps = {
  courts: Court[];
  selectedCourtId: number | null;
  onSelectCourt: (id: number) => void;
};

const courtIcon = L.divIcon({
  className: "court-map-marker",
  html: '<div class="court-map-marker-inner"></div>',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
});

function MapUpdater({ courts }: { courts: Court[] }) {
  const map = useMap();

  useEffect(() => {
    const validCourts = courts.filter(
      (court) =>
        court.lat != null &&
        court.lng != null &&
        Number.isFinite(court.lat) &&
        Number.isFinite(court.lng) &&
        court.lat >= -90 &&
        court.lat <= 90 &&
        court.lng >= -180 &&
        court.lng <= 180,
    );

    if (validCourts.length === 1) {
      map.setView([validCourts[0].lat!, validCourts[0].lng!], 14);
    } else if (validCourts.length > 1) {
      map.fitBounds(
        validCourts.map((court) => [court.lat!, court.lng!] as [number, number]),
        { padding: [35, 35], maxZoom: 14 },
      );
    }
  }, [courts, map]);

  return null;
}

export default function CourtMap({
  courts,
  selectedCourtId,
  onSelectCourt,
}: CourtMapProps) {
  const validCourts = courts.filter(
    (court) =>
      court.lat != null &&
      court.lng != null &&
      Number.isFinite(court.lat) &&
      Number.isFinite(court.lng) &&
      court.lat >= -90 &&
      court.lat <= 90 &&
      court.lng >= -180 &&
      court.lng <= 180,
  );

  return (
    <div className="court-map">
      <MapContainer
        center={[42.3601, -71.0589]}
        zoom={11}
        scrollWheelZoom
        className="court-map-canvas"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapUpdater courts={validCourts} />

        {validCourts.map((court) => (
          <Marker
            key={court.id}
            position={[court.lat!, court.lng!]}
            icon={courtIcon}
            eventHandlers={{
              click: () => onSelectCourt(court.id),
            }}
          >
            <Popup>
              <div className="court-map-popup">
                <strong>{court.name}</strong>
                <div>{court.address ?? court.sport}</div>
                <button
                  type="button"
                  onClick={() => onSelectCourt(court.id)}
                >
                  {selectedCourtId === court.id ? "Selected" : "View court"}
                </button>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {validCourts.length === 0 && (
        <div className="court-map-empty">
          No courts have valid map coordinates yet.
          <br />
          Courts will appear here once coordinates are added.
        </div>
      )}
    </div>
  );
}
