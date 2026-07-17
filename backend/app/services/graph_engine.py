import heapq
from app.db.sqlite_client import get_sqlite_conn


def get_metro_route(source_name: str, destination_name: str):
    """
    Computes the shortest route (based on travel time) between the source and
    destination metro stations using Dijkstra's algorithm.
    Reads station, connection, and interchange graphs dynamically from SQLite.
    """
    with get_sqlite_conn() as conn:
        stations = conn.execute("SELECT id, name, line FROM stations").fetchall()
        connections = conn.execute(
            "SELECT station_a_id, station_b_id, travel_time_minutes, fare_inr FROM connections"
        ).fetchall()
        interchanges = conn.execute(
            "SELECT station_from_id, station_to_id, transfer_time_minutes FROM interchanges"
        ).fetchall()

    station_by_id = {row["id"]: {"name": row["name"], "line": row["line"]} for row in stations}

    source_ids = [row["id"] for row in stations if row["name"].lower() == source_name.strip().lower()]
    dest_ids = [row["id"] for row in stations if row["name"].lower() == destination_name.strip().lower()]

    if not source_ids:
        raise ValueError(f"Source station '{source_name}' not found")
    if not dest_ids:
        raise ValueError(f"Destination station '{destination_name}' not found")

    dest_id_set = set(dest_ids)

    # Adjacency list: node_id -> list of (neighbor_id, weight_minutes, fare, edge_type)
    graph = {sid: [] for sid in station_by_id}

    for c in connections:
        a, b, t, f = c["station_a_id"], c["station_b_id"], c["travel_time_minutes"], c["fare_inr"]
        graph[a].append((b, t, f, "train"))
        # Both directions are already stored explicitly in the connections table per schema.

    for i in interchanges:
        f_id, t_id, tt = i["station_from_id"], i["station_to_id"], i["transfer_time_minutes"]
        graph[f_id].append((t_id, tt, 0, "walk"))
        graph[t_id].append((f_id, tt, 0, "walk"))  # walking is possible in both directions

    # Dijkstra, supporting multiple source nodes (same station name across lines)
    dist = {sid: float("inf") for sid in station_by_id}
    prev = {}
    prev_edge = {}
    visited = set()
    pq = []

    for sid in source_ids:
        dist[sid] = 0
        heapq.heappush(pq, (0, sid))

    while pq:
        d, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        for v, w, fare, edge_type in graph[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                prev_edge[v] = (w, fare, edge_type)
                heapq.heappush(pq, (nd, v))

    reachable_dest = [d for d in dest_ids if dist[d] < float("inf")]
    if not reachable_dest:
        raise ValueError(f"No route found between '{source_name}' and '{destination_name}'")

    best_dest = min(reachable_dest, key=lambda d: dist[d])

    # Reconstruct path
    path_ids = [best_dest]
    node = best_dest
    while node in prev:
        node = prev[node]
        path_ids.append(node)
    path_ids.reverse()

    total_fare = 0
    raw_route = []
    for idx, sid in enumerate(path_ids):
        st = station_by_id[sid]
        entry = {"station": st["name"], "line": st["line"]}
        if idx > 0:
            w, fare, edge_type = prev_edge[sid]
            entry["segment_type"] = edge_type
            if edge_type == "train":
                entry["segment_fare_inr"] = fare
                total_fare += fare
        raw_route.append(entry)

    # Build ordered_itinerary: mark a node as an interchange if the NEXT
    # hop from it is a walking transfer (i.e. it's where the passenger
    # changes lines), and note which line they transfer to.
    ordered_itinerary = []
    interchanges_count = 0
    for idx, entry in enumerate(raw_route):
        node = {
            "station_name": entry["station"],
            "line": entry["line"],
            "is_interchange": False,
            "transfer_to": None,
        }
        if idx + 1 < len(raw_route) and raw_route[idx + 1].get("segment_type") == "walk":
            node["is_interchange"] = True
            node["transfer_to"] = raw_route[idx + 1]["line"]
            interchanges_count += 1
        ordered_itinerary.append(node)

    return {
        "route_summary": {
            "source": source_name,
            "destination": destination_name,
            "total_travel_time_minutes": dist[best_dest],
            "total_fare_inr": total_fare,
            "interchanges_count": interchanges_count,
        },
        "ordered_itinerary": ordered_itinerary,
    }