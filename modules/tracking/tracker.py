from typing import List, Tuple, Dict
import numpy as np
from shared.schemas import Detection, Track, ObjectClass

def compute_iou(box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    w = max(0, x2 - x1)
    h = max(0, y2 - y1)
    inter_area = w * h

    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])

    union_area = area1 + area2 - inter_area
    if union_area <= 0:
        return 0.0
    return inter_area / union_area

def match_iou(tracks: List["STrack"], detections: List[Detection], iou_thresh: float = 0.2):
    if not tracks or not detections:
        return [], list(range(len(tracks))), list(range(len(detections)))

    iou_matrix = np.zeros((len(tracks), len(detections)), dtype=np.float32)
    for i, trk in enumerate(tracks):
        for j, det in enumerate(detections):
            if trk.cls == det.cls:  # Only match same class
                iou_matrix[i, j] = compute_iou(trk.bbox, det.bbox)

    try:
        from scipy.optimize import linear_sum_assignment
        row_ind, col_ind = linear_sum_assignment(-iou_matrix)
    except Exception:
        # Fallback greedy matching
        row_ind, col_ind = [], []
        used_cols = set()
        for r in range(len(tracks)):
            best_c = -1
            best_val = iou_thresh
            for c in range(len(detections)):
                if c not in used_cols and iou_matrix[r, c] > best_val:
                    best_val = iou_matrix[r, c]
                    best_c = c
            if best_c != -1:
                row_ind.append(r)
                col_ind.append(best_c)
                used_cols.add(best_c)
        row_ind, col_ind = np.array(row_ind), np.array(col_ind)

    matches = []
    unmatched_tracks = list(range(len(tracks)))
    unmatched_dets = list(range(len(detections)))

    for r, c in zip(row_ind, col_ind):
        if iou_matrix[r, c] >= iou_thresh:
            matches.append((r, c))
            if r in unmatched_tracks:
                unmatched_tracks.remove(r)
            if c in unmatched_dets:
                unmatched_dets.remove(c)

    return matches, unmatched_tracks, unmatched_dets

class STrack:
    def __init__(self, track_id: int, bbox: Tuple[int, int, int, int], cls: ObjectClass, conf: float, frame_id: int):
        self.track_id = track_id
        self.bbox = bbox
        self.cls = cls
        self.conf = conf
        self.frame_id = frame_id
        self.state = "tracked"  # "tracked", "lost"

    def update(self, detection: Detection, frame_id: int):
        self.bbox = detection.bbox
        self.conf = detection.conf
        self.frame_id = frame_id
        self.state = "tracked"

class ByteTracker:
    def __init__(self, track_thresh: float = 0.3, low_thresh: float = 0.1, max_time_lost: int = 30):
        self.track_thresh = track_thresh
        self.low_thresh = low_thresh
        self.max_time_lost = max_time_lost
        
        self.tracked_stracks: List[STrack] = []
        self.lost_stracks: List[STrack] = []
        self.frame_id = 0
        self.next_id = 1

    def update(self, detections: List[Detection]) -> List[Track]:
        self.frame_id += 1

        dets_high = [d for d in detections if d.conf >= self.track_thresh]
        dets_low = [d for d in detections if self.low_thresh <= d.conf < self.track_thresh]

        # 1. Match high-conf detections with active tracked tracks
        matches_high, unmatch_trks, unmatch_dets_high = match_iou(self.tracked_stracks, dets_high, iou_thresh=0.2)

        for trk_idx, det_idx in matches_high:
            self.tracked_stracks[trk_idx].update(dets_high[det_idx], self.frame_id)

        # 2. Match remaining unmatched tracked tracks with low-conf detections
        unmatched_stracks = [self.tracked_stracks[i] for i in unmatch_trks]
        matches_low, unmatch_trks_low, _ = match_iou(unmatched_stracks, dets_low, iou_thresh=0.2)

        for trk_idx, det_idx in matches_low:
            unmatched_stracks[trk_idx].update(dets_low[det_idx], self.frame_id)

        # 3. Match unmatched high-conf detections with lost tracks (re-identification)
        lost_candidates = [t for t in self.lost_stracks if t.state == "lost"]
        unmatched_high_dets = [dets_high[i] for i in unmatch_dets_high]
        matches_lost, _, unmatch_dets_lost = match_iou(lost_candidates, unmatched_high_dets, iou_thresh=0.2)

        for trk_idx, det_idx in matches_lost:
            track = lost_candidates[trk_idx]
            track.update(unmatched_high_dets[det_idx], self.frame_id)
            if track in self.lost_stracks:
                self.lost_stracks.remove(track)
            if track not in self.tracked_stracks:
                self.tracked_stracks.append(track)

        # 4. Mark remaining unmatched active tracks as lost
        still_unmatched = [unmatched_stracks[i] for i in unmatch_trks_low]
        for trk in still_unmatched:
            if trk not in matches_high: # check not updated
                trk.state = "lost"
                if trk in self.tracked_stracks:
                    self.tracked_stracks.remove(trk)
                if trk not in self.lost_stracks:
                    self.lost_stracks.append(trk)

        # 5. Create new tracks for remaining unmatched high-conf detections
        new_dets = [unmatched_high_dets[i] for i in unmatch_dets_lost]
        for det in new_dets:
            new_track = STrack(self.next_id, det.bbox, det.cls, det.conf, self.frame_id)
            self.next_id += 1
            self.tracked_stracks.append(new_track)

        # 6. Remove lost tracks that exceeded max_time_lost
        self.lost_stracks = [t for t in self.lost_stracks if (self.frame_id - t.frame_id) <= self.max_time_lost]

        # 7. Build output Track list
        output_tracks = []
        for trk in self.tracked_stracks:
            if trk.state == "tracked":
                output_tracks.append(Track(
                    track_id=trk.track_id,
                    bbox=trk.bbox,
                    cls=trk.cls,
                    conf=trk.conf
                ))
        return output_tracks
