-- SQL for table: community_replies
-- Generated: 2025-05-15 17:44:41
-- Row count: 6

CREATE TABLE IF NOT EXISTS "community_replies" (
    "id" SERIAL PRIMARY KEY,
    "thread_id" INTEGER NOT NULL,
    "user_id" INTEGER NOT NULL,
    "content" TEXT NOT NULL,
    "is_anonymous" BOOLEAN NULL,
    "is_doctor_response" BOOLEAN NULL,
    "created_at" TIMESTAMP NULL,
    "upvotes" INTEGER NULL,
    "parent_reply_id" INTEGER NULL,
    "is_expert_advice" BOOLEAN NULL,
    "is_ai_response" BOOLEAN NULL,
    "photo_url" TEXT NULL,
    "video_url" TEXT NULL
);

INSERT INTO "community_replies" ("id", "thread_id", "user_id", "content", "is_anonymous", "is_doctor_response", "created_at", "upvotes", "parent_reply_id", "is_expert_advice", "is_ai_response", "photo_url", "video_url") VALUES
(1, 1, 14, 'I had rhinoplasty about a year ago and your experience sounds very similar to mine. The psychological aspect was definitely the hardest part! That "middle phase" where you''re still swollen but the initial excitement has worn off was tough.

One thing I wish I''d known was how much the tip of my nose would change over time. It took almost a full year for it to reach its final shape, which was longer than I expected.

Overall though, I''m very happy with my decision. My breathing is so much better now (I had a deviated septum), and I feel more confident in photos.', False, False, '2025-04-24 20:16:38.010897', 5, NULL, False, False, NULL, NULL),
(2, 2, 79, 'Thanks for sharing such a detailed timeline! I''m scheduled for BA next month and this helps me know what to expect.

Question - did you find that you needed help at home during the first week? I live alone and am trying to decide if I should have someone stay with me.', False, False, '2025-05-03 20:21:08.203152', 3, NULL, False, False, NULL, NULL),
(3, 2, 63, 'I had my BA about 3 months ago and your timeline is spot on! The "drop and fluff" is real - mine looked so unnatural at first but now they''ve settled beautifully.

One thing I''d add is that I experienced random sharp pains (like nerve zings) around week 5-8 as everything was healing. My surgeon said this was normal nerve regeneration.

Also, sleeping was difficult for me for almost 6 weeks. I had to sleep on my back with pillows on either side to prevent accidentally rolling onto my side or stomach.', False, False, '2025-04-30 20:21:08.203152', 4, NULL, False, False, NULL, NULL),
(5, 4, 35, 'I had a tummy tuck 2 years after my second C-section, and the surgeon was able to completely remove my C-section scar as part of the procedure. The new tummy tuck scar is lower and thinner than my old C-section scar was.

One thing to note is that if you have any numbness around your C-section scar (which is common), you''ll likely have a larger numb area after the tummy tuck. I have numbness from hip to hip above the new scar, but it doesn''t bother me.

Recovery wasn''t harder because of my previous surgeries. In fact, my surgeon said the internal scar tissue from C-sections can sometimes provide additional support for the muscle repair.

I waited 3 years after my last pregnancy before getting the tummy tuck. My surgeon recommended waiting until I''d been at a stable weight for at least 6 months.', False, False, '2025-05-17 20:22:52.801644', 6, NULL, False, False, NULL, NULL),
(6, 5, 122, 'My bruising after lipo on similar areas lasted about 3 weeks total, but it faded gradually. By the end of the second week, it was yellow rather than purple/blue and much less noticeable.

What helped me: arnica (like you''re doing), gentle walking to increase circulation, and staying super hydrated. My doctor also recommended pineapple for its bromelain content, which may help with swelling.

As for the compression garment, I wore mine 24/7 for 4 weeks, then only during the day for 2 more weeks. Don''t rush taking it off - it really helps with skin retraction and reducing swelling!', True, False, '2025-05-15 20:23:02.544529', 4, NULL, False, False, NULL, NULL),
(7, 6, 84, 'I had upper and lower blepharoplasty at 54, and it was one of the best decisions I''ve made. I''m now 58 and still very happy with the results.

As for how much younger it made me look - people consistently guess my age about 7-10 years younger than I am. But more importantly, I no longer look perpetually tired or sad. Friends and coworkers said I looked "refreshed" rather than "different," which is exactly what I wanted.

Recovery: I had significant bruising that lasted about 2 weeks. I was comfortable running errands with sunglasses after 10 days. At 3 weeks, makeup easily covered any remaining discoloration.

I did experience dry eyes for about 3 months, but using preservative-free eye drops helped tremendously. This resolved completely.

My advice: Find a surgeon who specializes in eyes specifically (oculoplastic surgeon or facial plastic surgeon with lots of eye experience), and be very clear about wanting natural results.', False, False, '2025-05-08 20:23:12.369693', 9, NULL, False, False, NULL, NULL);

SELECT setval(pg_get_serial_sequence('community_replies', 'id'), 7, true);

