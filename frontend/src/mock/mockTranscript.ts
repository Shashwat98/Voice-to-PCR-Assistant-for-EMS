import type { TranscriptSegment } from '../types/session';

const base = '2026-04-03T10:00:00Z';
const t = (offsetSec: number) =>
  new Date(new Date(base).getTime() + offsetSec * 1000).toISOString();

export const mockTranscriptSegments: TranscriptSegment[] = [
  {
    text: 'Medic 7 to County, coming in with a 71-year-old male.',
    start_time: 0,
    end_time: 4.2,
    timestamp: t(0),
  },
  {
    text: 'Chief complaint chest pain, onset about 20 minutes ago at rest.',
    start_time: 4.5,
    end_time: 9.1,
    timestamp: t(5),
  },
  {
    text: 'History of CAD and hypertension. Patient is on metoprolol and aspirin.',
    start_time: 9.5,
    end_time: 15.3,
    timestamp: t(10),
  },
  {
    text: 'Allergic to penicillin.',
    start_time: 15.8,
    end_time: 17.2,
    timestamp: t(16),
  },
  {
    text: 'Vitals: BP 158 over 94, heart rate 96, respiratory rate 18, sats 94%, GCS 15, alert.',
    start_time: 18.0,
    end_time: 26.4,
    timestamp: t(18),
  },
  {
    text: 'Pain 8 out of 10. 12-lead shows ST elevation V2 through V4, transmitted en route.',
    start_time: 27.0,
    end_time: 34.1,
    timestamp: t(27),
  },
  {
    text: 'Gave 324 aspirin PO and 0.4 nitro SL. IV access established.',
    start_time: 35.0,
    end_time: 41.5,
    timestamp: t(35),
  },
  {
    text: 'Impression angina, possible STEMI. ETA 6 minutes.',
    start_time: 42.0,
    end_time: 46.8,
    timestamp: t(42),
  },
];
