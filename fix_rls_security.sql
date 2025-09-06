-- Fix Row Level Security (RLS) for all tables in Antidote platform
-- This script enables RLS and creates appropriate security policies

-- Enable RLS on all tables
ALTER TABLE public.body_parts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.doctors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.face_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_badges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_reputation ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recommendation_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.banners ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clinic_billing ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clinic_consultations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.banner_slides ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.procedures ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.doctor_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.face_analysis_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.face_scan_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.doctor_photos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.doctor_availability ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.doctor_procedures ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.community ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.education_modules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.review_replies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.community_replies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.community_tagging ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.thread_votes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reddit_imports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.professional_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.post_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.thread_saves ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.thread_follows ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.thread_reactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.thread_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.module_quizzes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.module_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reply_votes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.community_moderation ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quiz_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quiz_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clinic_doctors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clinic_specialties ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clinic_photos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clinic_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clinic_procedures ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clinic_amenities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clinic_leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clinic_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.procedure_gallery ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clinic_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.enhanced_leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clinic_premium_placements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.otp_verifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lead_billing ENABLE ROW LEVEL SECURITY;

-- Create security policies for public data (tables that should be readable by all authenticated users)
-- Body Parts and Categories - Public readable
CREATE POLICY "Body parts are viewable by everyone" ON public.body_parts FOR SELECT USING (true);
CREATE POLICY "Categories are viewable by everyone" ON public.categories FOR SELECT USING (true);
CREATE POLICY "Procedures are viewable by everyone" ON public.procedures FOR SELECT USING (true);
CREATE POLICY "Doctor profiles are viewable by everyone" ON public.doctors FOR SELECT USING (true);
CREATE POLICY "Doctor photos are viewable by everyone" ON public.doctor_photos FOR SELECT USING (true);
CREATE POLICY "Doctor availability is viewable by everyone" ON public.doctor_availability FOR SELECT USING (true);
CREATE POLICY "Doctor procedures are viewable by everyone" ON public.doctor_procedures FOR SELECT USING (true);
CREATE POLICY "Doctor categories are viewable by everyone" ON public.doctor_categories FOR SELECT USING (true);
CREATE POLICY "Reviews are viewable by everyone" ON public.reviews FOR SELECT USING (true);
CREATE POLICY "Review replies are viewable by everyone" ON public.review_replies FOR SELECT USING (true);
CREATE POLICY "Banners are viewable by everyone" ON public.banners FOR SELECT USING (true);
CREATE POLICY "Banner slides are viewable by everyone" ON public.banner_slides FOR SELECT USING (true);
CREATE POLICY "Education modules are viewable by everyone" ON public.education_modules FOR SELECT USING (true);
CREATE POLICY "Module quizzes are viewable by everyone" ON public.module_quizzes FOR SELECT USING (true);
CREATE POLICY "Quiz questions are viewable by everyone" ON public.quiz_questions FOR SELECT USING (true);
CREATE POLICY "Procedure gallery is viewable by everyone" ON public.procedure_gallery FOR SELECT USING (true);

-- User-specific data policies (users can only access their own data)
CREATE POLICY "Users can view own profile" ON public.users FOR SELECT USING (auth.uid() = id::text);
CREATE POLICY "Users can update own profile" ON public.users FOR UPDATE USING (auth.uid() = id::text);

CREATE POLICY "Users can view own preferences" ON public.user_preferences FOR SELECT USING (auth.uid() = user_id::text);
CREATE POLICY "Users can update own preferences" ON public.user_preferences FOR ALL USING (auth.uid() = user_id::text);

CREATE POLICY "Users can view own notifications" ON public.notifications FOR SELECT USING (auth.uid() = user_id::text);
CREATE POLICY "Users can update own notifications" ON public.notifications FOR UPDATE USING (auth.uid() = user_id::text);

CREATE POLICY "Users can view own badges" ON public.user_badges FOR SELECT USING (auth.uid() = user_id::text);
CREATE POLICY "Users can view own reputation" ON public.user_reputation FOR SELECT USING (auth.uid() = user_id::text);
CREATE POLICY "Users can view own user profile" ON public.user_profiles FOR SELECT USING (auth.uid() = user_id::text);
CREATE POLICY "Users can update own user profile" ON public.user_profiles FOR ALL USING (auth.uid() = user_id::text);

CREATE POLICY "Users can view own face analyses" ON public.face_analyses FOR SELECT USING (auth.uid() = user_id::text);
CREATE POLICY "Users can create own face analyses" ON public.face_analyses FOR INSERT WITH CHECK (auth.uid() = user_id::text);

CREATE POLICY "Users can view own face analysis recommendations" ON public.face_analysis_recommendations FOR SELECT USING (auth.uid() = (SELECT user_id::text FROM public.face_analyses WHERE id = face_analysis_id));

CREATE POLICY "Users can view own face scan recommendations" ON public.face_scan_recommendations FOR SELECT USING (auth.uid() = user_id::text);
CREATE POLICY "Users can create own face scan recommendations" ON public.face_scan_recommendations FOR INSERT WITH CHECK (auth.uid() = user_id::text);

CREATE POLICY "Users can view own interactions" ON public.interactions FOR SELECT USING (auth.uid() = user_id::text);
CREATE POLICY "Users can create own interactions" ON public.interactions FOR INSERT WITH CHECK (auth.uid() = user_id::text);

CREATE POLICY "Users can view own messages" ON public.messages FOR SELECT USING (auth.uid() = sender_id::text OR auth.uid() = recipient_id::text);
CREATE POLICY "Users can send messages" ON public.messages FOR INSERT WITH CHECK (auth.uid() = sender_id::text);

CREATE POLICY "Users can view own recommendation history" ON public.recommendation_history FOR SELECT USING (auth.uid() = user_id::text);
CREATE POLICY "Users can create own recommendation history" ON public.recommendation_history FOR INSERT WITH CHECK (auth.uid() = user_id::text);

CREATE POLICY "Users can view own appointments" ON public.appointments FOR SELECT USING (auth.uid() = user_id::text);
CREATE POLICY "Users can create own appointments" ON public.appointments FOR INSERT WITH CHECK (auth.uid() = user_id::text);
CREATE POLICY "Users can update own appointments" ON public.appointments FOR UPDATE USING (auth.uid() = user_id::text);

CREATE POLICY "Users can view own favorites" ON public.favorites FOR SELECT USING (auth.uid() = user_id::text);
CREATE POLICY "Users can manage own favorites" ON public.favorites FOR ALL USING (auth.uid() = user_id::text);

CREATE POLICY "Users can view own OTP verifications" ON public.otp_verifications FOR SELECT USING (auth.uid() = user_id::text);
CREATE POLICY "Users can create own OTP verifications" ON public.otp_verifications FOR INSERT WITH CHECK (auth.uid() = user_id::text);

-- Community features policies
CREATE POLICY "Community posts are viewable by everyone" ON public.community FOR SELECT USING (true);
CREATE POLICY "Users can create community posts" ON public.community FOR INSERT WITH CHECK (auth.uid() = user_id::text);
CREATE POLICY "Users can update own community posts" ON public.community FOR UPDATE USING (auth.uid() = user_id::text);

CREATE POLICY "Threads are viewable by everyone" ON public.threads FOR SELECT USING (true);
CREATE POLICY "Users can create threads" ON public.threads FOR INSERT WITH CHECK (auth.uid() = user_id::text);
CREATE POLICY "Users can update own threads" ON public.threads FOR UPDATE USING (auth.uid() = user_id::text);

CREATE POLICY "Community replies are viewable by everyone" ON public.community_replies FOR SELECT USING (true);
CREATE POLICY "Users can create community replies" ON public.community_replies FOR INSERT WITH CHECK (auth.uid() = user_id::text);
CREATE POLICY "Users can update own community replies" ON public.community_replies FOR UPDATE USING (auth.uid() = user_id::text);

CREATE POLICY "Community tagging is viewable by everyone" ON public.community_tagging FOR SELECT USING (true);
CREATE POLICY "Users can create community tags" ON public.community_tagging FOR INSERT WITH CHECK (true);

CREATE POLICY "Thread votes are viewable by everyone" ON public.thread_votes FOR SELECT USING (true);
CREATE POLICY "Users can vote on threads" ON public.thread_votes FOR ALL USING (auth.uid() = user_id::text);

CREATE POLICY "Reply votes are viewable by everyone" ON public.reply_votes FOR SELECT USING (true);
CREATE POLICY "Users can vote on replies" ON public.reply_votes FOR ALL USING (auth.uid() = user_id::text);

CREATE POLICY "Users can view own thread saves" ON public.thread_saves FOR SELECT USING (auth.uid() = user_id::text);
CREATE POLICY "Users can manage own thread saves" ON public.thread_saves FOR ALL USING (auth.uid() = user_id::text);

CREATE POLICY "Users can view own thread follows" ON public.thread_follows FOR SELECT USING (auth.uid() = user_id::text);
CREATE POLICY "Users can manage own thread follows" ON public.thread_follows FOR ALL USING (auth.uid() = user_id::text);

CREATE POLICY "Thread reactions are viewable by everyone" ON public.thread_reactions FOR SELECT USING (true);
CREATE POLICY "Users can manage own thread reactions" ON public.thread_reactions FOR ALL USING (auth.uid() = user_id::text);

CREATE POLICY "Thread analytics are viewable by everyone" ON public.thread_analytics FOR SELECT USING (true);

CREATE POLICY "Users can view own user achievements" ON public.user_achievements FOR SELECT USING (auth.uid() = user_id::text);
CREATE POLICY "Users can view own module progress" ON public.module_progress FOR SELECT USING (auth.uid() = user_id::text);
CREATE POLICY "Users can update own module progress" ON public.module_progress FOR ALL USING (auth.uid() = user_id::text);

CREATE POLICY "Users can view own quiz attempts" ON public.quiz_attempts FOR SELECT USING (auth.uid() = user_id::text);
CREATE POLICY "Users can create own quiz attempts" ON public.quiz_attempts FOR INSERT WITH CHECK (auth.uid() = user_id::text);

-- Professional/Doctor specific policies
CREATE POLICY "Professional responses are viewable by everyone" ON public.professional_responses FOR SELECT USING (true);
CREATE POLICY "Doctors can create professional responses" ON public.professional_responses FOR INSERT WITH CHECK (auth.uid() = doctor_id::text);
CREATE POLICY "Doctors can update own professional responses" ON public.professional_responses FOR UPDATE USING (auth.uid() = doctor_id::text);

-- Admin/System policies (restrictive by default)
CREATE POLICY "Reddit imports viewable by authenticated users" ON public.reddit_imports FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Post categories viewable by everyone" ON public.post_categories FOR SELECT USING (true);
CREATE POLICY "Community moderation viewable by authenticated users" ON public.community_moderation FOR SELECT USING (auth.role() = 'authenticated');

-- Clinic-related policies
CREATE POLICY "Clinic doctors are viewable by everyone" ON public.clinic_doctors FOR SELECT USING (true);
CREATE POLICY "Clinic specialties are viewable by everyone" ON public.clinic_specialties FOR SELECT USING (true);
CREATE POLICY "Clinic photos are viewable by everyone" ON public.clinic_photos FOR SELECT USING (true);
CREATE POLICY "Clinic reviews are viewable by everyone" ON public.clinic_reviews FOR SELECT USING (true);
CREATE POLICY "Clinic procedures are viewable by everyone" ON public.clinic_procedures FOR SELECT USING (true);
CREATE POLICY "Clinic amenities are viewable by everyone" ON public.clinic_amenities FOR SELECT USING (true);

-- Billing and lead policies (restrictive)
CREATE POLICY "Clinic billing viewable by clinic owners" ON public.clinic_billing FOR SELECT USING (false); -- Implement proper clinic ownership check
CREATE POLICY "Clinic consultations viewable by clinic owners" ON public.clinic_consultations FOR SELECT USING (false); -- Implement proper clinic ownership check
CREATE POLICY "Clinic leads viewable by clinic owners" ON public.clinic_leads FOR SELECT USING (false); -- Implement proper clinic ownership check
CREATE POLICY "Enhanced leads viewable by clinic owners" ON public.enhanced_leads FOR SELECT USING (false); -- Implement proper clinic ownership check
CREATE POLICY "Lead billing viewable by clinic owners" ON public.lead_billing FOR SELECT USING (false); -- Implement proper clinic ownership check
CREATE POLICY "Clinic activities viewable by clinic owners" ON public.clinic_activities FOR SELECT USING (false); -- Implement proper clinic ownership check
CREATE POLICY "Clinic subscriptions viewable by clinic owners" ON public.clinic_subscriptions FOR SELECT USING (false); -- Implement proper clinic ownership check
CREATE POLICY "Clinic premium placements viewable by clinic owners" ON public.clinic_premium_placements FOR SELECT USING (false); -- Implement proper clinic ownership check

-- Note: The clinic-related policies above use 'false' as a placeholder.
-- You'll need to implement proper clinic ownership checks based on your user authentication system.
-- For example: auth.uid() = (SELECT owner_id FROM clinics WHERE id = clinic_id)