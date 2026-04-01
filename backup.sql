--
-- PostgreSQL database dump
--

\restrict 862w7VtVCieRcGagyHvLHq7tdga2yUozIpDrlAfbBx1vxB6052Vb9jglljoIdbO

-- Dumped from database version 18.3 (Debian 18.3-1.pgdg12+1)
-- Dumped by pg_dump version 18.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: the_commons_db_user
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO the_commons_db_user;

--
-- Name: algorithmmode; Type: TYPE; Schema: public; Owner: the_commons_db_user
--

CREATE TYPE public.algorithmmode AS ENUM (
    'TRANSPARENT',
    'CHRONOLOGICAL',
    'COMMUNITY'
);


ALTER TYPE public.algorithmmode OWNER TO the_commons_db_user;

--
-- Name: poststatus; Type: TYPE; Schema: public; Owner: the_commons_db_user
--

CREATE TYPE public.poststatus AS ENUM (
    'PENDING',
    'PUBLISHED',
    'HELD',
    'REMOVED',
    'APPEALED'
);


ALTER TYPE public.poststatus OWNER TO the_commons_db_user;

--
-- Name: posttype; Type: TYPE; Schema: public; Owner: the_commons_db_user
--

CREATE TYPE public.posttype AS ENUM (
    'TEXT',
    'IMAGE',
    'VIDEO',
    'AUDIO',
    'LIVE'
);


ALTER TYPE public.posttype OWNER TO the_commons_db_user;

--
-- Name: userrole; Type: TYPE; Schema: public; Owner: the_commons_db_user
--

CREATE TYPE public.userrole AS ENUM (
    'USER',
    'CREATOR',
    'SELLER',
    'CIRCLE',
    'SOVEREIGN'
);


ALTER TYPE public.userrole OWNER TO the_commons_db_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: circle_decisions; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.circle_decisions (
    id integer NOT NULL,
    subject character varying(255),
    decision_type character varying(50),
    post_id integer,
    outcome character varying(50),
    ayes integer,
    nays integer,
    abstentions integer,
    dissent_notes text,
    reasoning text,
    created_at timestamp without time zone,
    closed_at timestamp without time zone
);


ALTER TABLE public.circle_decisions OWNER TO the_commons_db_user;

--
-- Name: circle_decisions_id_seq; Type: SEQUENCE; Schema: public; Owner: the_commons_db_user
--

CREATE SEQUENCE public.circle_decisions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.circle_decisions_id_seq OWNER TO the_commons_db_user;

--
-- Name: circle_decisions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: the_commons_db_user
--

ALTER SEQUENCE public.circle_decisions_id_seq OWNED BY public.circle_decisions.id;


--
-- Name: circle_members; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.circle_members (
    id integer NOT NULL,
    user_id integer,
    seat_type character varying(50),
    region character varying(100),
    is_head boolean,
    elected_at timestamp without time zone,
    term_ends timestamp without time zone,
    votes_cast integer
);


ALTER TABLE public.circle_members OWNER TO the_commons_db_user;

--
-- Name: circle_members_id_seq; Type: SEQUENCE; Schema: public; Owner: the_commons_db_user
--

CREATE SEQUENCE public.circle_members_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.circle_members_id_seq OWNER TO the_commons_db_user;

--
-- Name: circle_members_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: the_commons_db_user
--

ALTER SEQUENCE public.circle_members_id_seq OWNED BY public.circle_members.id;


--
-- Name: community_votes; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.community_votes (
    id integer NOT NULL,
    post_id integer NOT NULL,
    user_id integer NOT NULL,
    value integer,
    created_at timestamp without time zone
);


ALTER TABLE public.community_votes OWNER TO the_commons_db_user;

--
-- Name: community_votes_id_seq; Type: SEQUENCE; Schema: public; Owner: the_commons_db_user
--

CREATE SEQUENCE public.community_votes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.community_votes_id_seq OWNER TO the_commons_db_user;

--
-- Name: community_votes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: the_commons_db_user
--

ALTER SEQUENCE public.community_votes_id_seq OWNED BY public.community_votes.id;


--
-- Name: fingerprint_records; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.fingerprint_records (
    id integer NOT NULL,
    post_id integer,
    scan_result character varying(20),
    claims_found text,
    deepfake_score double precision,
    manipulation_score double precision,
    reviewer character varying(100),
    reviewer_notes text,
    decision character varying(20),
    decision_reason text,
    scanned_at timestamp without time zone,
    decided_at timestamp without time zone
);


ALTER TABLE public.fingerprint_records OWNER TO the_commons_db_user;

--
-- Name: fingerprint_records_id_seq; Type: SEQUENCE; Schema: public; Owner: the_commons_db_user
--

CREATE SEQUENCE public.fingerprint_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fingerprint_records_id_seq OWNER TO the_commons_db_user;

--
-- Name: fingerprint_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: the_commons_db_user
--

ALTER SEQUENCE public.fingerprint_records_id_seq OWNED BY public.fingerprint_records.id;


--
-- Name: listing_messages; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.listing_messages (
    id integer NOT NULL,
    listing_id integer NOT NULL,
    sender_id integer NOT NULL,
    recipient_id integer NOT NULL,
    body text NOT NULL,
    is_read boolean,
    created_at timestamp without time zone
);


ALTER TABLE public.listing_messages OWNER TO the_commons_db_user;

--
-- Name: listing_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: the_commons_db_user
--

CREATE SEQUENCE public.listing_messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.listing_messages_id_seq OWNER TO the_commons_db_user;

--
-- Name: listing_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: the_commons_db_user
--

ALTER SEQUENCE public.listing_messages_id_seq OWNED BY public.listing_messages.id;


--
-- Name: listings; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.listings (
    id integer NOT NULL,
    title text NOT NULL,
    description text,
    price double precision NOT NULL,
    media_path text,
    seller_id integer NOT NULL,
    is_active boolean,
    created_at timestamp without time zone
);


ALTER TABLE public.listings OWNER TO the_commons_db_user;

--
-- Name: listings_id_seq; Type: SEQUENCE; Schema: public; Owner: the_commons_db_user
--

CREATE SEQUENCE public.listings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.listings_id_seq OWNER TO the_commons_db_user;

--
-- Name: listings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: the_commons_db_user
--

ALTER SEQUENCE public.listings_id_seq OWNED BY public.listings.id;


--
-- Name: magic_tokens; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.magic_tokens (
    token character varying NOT NULL,
    email character varying NOT NULL,
    expires timestamp without time zone NOT NULL
);


ALTER TABLE public.magic_tokens OWNER TO the_commons_db_user;

--
-- Name: order_items; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.order_items (
    id integer NOT NULL,
    order_id integer,
    product_id integer,
    quantity integer,
    item_price double precision NOT NULL,
    line_total double precision NOT NULL
);


ALTER TABLE public.order_items OWNER TO the_commons_db_user;

--
-- Name: order_items_id_seq; Type: SEQUENCE; Schema: public; Owner: the_commons_db_user
--

CREATE SEQUENCE public.order_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.order_items_id_seq OWNER TO the_commons_db_user;

--
-- Name: order_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: the_commons_db_user
--

ALTER SEQUENCE public.order_items_id_seq OWNED BY public.order_items.id;


--
-- Name: orders; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.orders (
    id integer NOT NULL,
    buyer_id integer,
    platform_fee double precision,
    items_total double precision NOT NULL,
    order_total double precision NOT NULL,
    status character varying(50),
    created_at timestamp without time zone
);


ALTER TABLE public.orders OWNER TO the_commons_db_user;

--
-- Name: orders_id_seq; Type: SEQUENCE; Schema: public; Owner: the_commons_db_user
--

CREATE SEQUENCE public.orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.orders_id_seq OWNER TO the_commons_db_user;

--
-- Name: orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: the_commons_db_user
--

ALTER SEQUENCE public.orders_id_seq OWNED BY public.orders.id;


--
-- Name: posts; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.posts (
    id integer NOT NULL,
    author_id integer NOT NULL,
    post_type public.posttype NOT NULL,
    content text,
    media_path character varying(500),
    status public.poststatus,
    is_news boolean,
    is_political boolean,
    community_score double precision,
    view_count integer,
    created_at timestamp without time zone,
    published_at timestamp without time zone
);


ALTER TABLE public.posts OWNER TO the_commons_db_user;

--
-- Name: posts_id_seq; Type: SEQUENCE; Schema: public; Owner: the_commons_db_user
--

CREATE SEQUENCE public.posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.posts_id_seq OWNER TO the_commons_db_user;

--
-- Name: posts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: the_commons_db_user
--

ALTER SEQUENCE public.posts_id_seq OWNED BY public.posts.id;


--
-- Name: product_tags; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.product_tags (
    id integer NOT NULL,
    post_id integer,
    product_id integer,
    timestamp_sec double precision
);


ALTER TABLE public.product_tags OWNER TO the_commons_db_user;

--
-- Name: product_tags_id_seq; Type: SEQUENCE; Schema: public; Owner: the_commons_db_user
--

CREATE SEQUENCE public.product_tags_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.product_tags_id_seq OWNER TO the_commons_db_user;

--
-- Name: product_tags_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: the_commons_db_user
--

ALTER SEQUENCE public.product_tags_id_seq OWNED BY public.product_tags.id;


--
-- Name: products; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.products (
    id integer NOT NULL,
    seller_id integer,
    name character varying(300),
    description text,
    price double precision NOT NULL,
    media_path character varying(500),
    is_active boolean,
    community_score double precision,
    created_at timestamp without time zone
);


ALTER TABLE public.products OWNER TO the_commons_db_user;

--
-- Name: products_id_seq; Type: SEQUENCE; Schema: public; Owner: the_commons_db_user
--

CREATE SEQUENCE public.products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.products_id_seq OWNER TO the_commons_db_user;

--
-- Name: products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: the_commons_db_user
--

ALTER SEQUENCE public.products_id_seq OWNED BY public.products.id;


--
-- Name: seller_profiles; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.seller_profiles (
    id integer NOT NULL,
    user_id integer,
    business_name character varying(200),
    business_type character varying(50),
    is_verified boolean,
    is_corporation boolean,
    is_publicly_traded boolean,
    approved_at timestamp without time zone
);


ALTER TABLE public.seller_profiles OWNER TO the_commons_db_user;

--
-- Name: seller_profiles_id_seq; Type: SEQUENCE; Schema: public; Owner: the_commons_db_user
--

CREATE SEQUENCE public.seller_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.seller_profiles_id_seq OWNER TO the_commons_db_user;

--
-- Name: seller_profiles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: the_commons_db_user
--

ALTER SEQUENCE public.seller_profiles_id_seq OWNED BY public.seller_profiles.id;


--
-- Name: surplus_donations; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.surplus_donations (
    id integer NOT NULL,
    period_start timestamp without time zone NOT NULL,
    period_end timestamp without time zone NOT NULL,
    operating_costs double precision NOT NULL,
    total_collected double precision NOT NULL,
    surplus_amount double precision NOT NULL,
    cause_name character varying(300) NOT NULL,
    cause_url character varying(500),
    cause_description text,
    donated_at timestamp without time zone,
    confirmed boolean,
    public_note text,
    designated_by character varying(100)
);


ALTER TABLE public.surplus_donations OWNER TO the_commons_db_user;

--
-- Name: surplus_donations_id_seq; Type: SEQUENCE; Schema: public; Owner: the_commons_db_user
--

CREATE SEQUENCE public.surplus_donations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.surplus_donations_id_seq OWNER TO the_commons_db_user;

--
-- Name: surplus_donations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: the_commons_db_user
--

ALTER SEQUENCE public.surplus_donations_id_seq OWNED BY public.surplus_donations.id;


--
-- Name: transactions; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.transactions (
    id integer NOT NULL,
    buyer_id integer,
    product_id integer,
    product_price double precision NOT NULL,
    platform_fee double precision,
    total double precision NOT NULL,
    status character varying(50),
    created_at timestamp without time zone
);


ALTER TABLE public.transactions OWNER TO the_commons_db_user;

--
-- Name: transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: the_commons_db_user
--

CREATE SEQUENCE public.transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.transactions_id_seq OWNER TO the_commons_db_user;

--
-- Name: transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: the_commons_db_user
--

ALTER SEQUENCE public.transactions_id_seq OWNED BY public.transactions.id;


--
-- Name: user_content_type_preferences; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.user_content_type_preferences (
    id integer NOT NULL,
    user_id integer NOT NULL,
    content_type character varying(50) NOT NULL,
    score double precision,
    updated_at timestamp without time zone
);


ALTER TABLE public.user_content_type_preferences OWNER TO the_commons_db_user;

--
-- Name: user_content_type_preferences_id_seq; Type: SEQUENCE; Schema: public; Owner: the_commons_db_user
--

CREATE SEQUENCE public.user_content_type_preferences_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_content_type_preferences_id_seq OWNER TO the_commons_db_user;

--
-- Name: user_content_type_preferences_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: the_commons_db_user
--

ALTER SEQUENCE public.user_content_type_preferences_id_seq OWNED BY public.user_content_type_preferences.id;


--
-- Name: user_creator_affinity; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.user_creator_affinity (
    id integer NOT NULL,
    user_id integer NOT NULL,
    creator_id integer NOT NULL,
    score double precision,
    updated_at timestamp without time zone
);


ALTER TABLE public.user_creator_affinity OWNER TO the_commons_db_user;

--
-- Name: user_creator_affinity_id_seq; Type: SEQUENCE; Schema: public; Owner: the_commons_db_user
--

CREATE SEQUENCE public.user_creator_affinity_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_creator_affinity_id_seq OWNER TO the_commons_db_user;

--
-- Name: user_creator_affinity_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: the_commons_db_user
--

ALTER SEQUENCE public.user_creator_affinity_id_seq OWNED BY public.user_creator_affinity.id;


--
-- Name: user_topic_preferences; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.user_topic_preferences (
    id integer NOT NULL,
    user_id integer NOT NULL,
    topic character varying(100) NOT NULL,
    score double precision,
    updated_at timestamp without time zone
);


ALTER TABLE public.user_topic_preferences OWNER TO the_commons_db_user;

--
-- Name: user_topic_preferences_id_seq; Type: SEQUENCE; Schema: public; Owner: the_commons_db_user
--

CREATE SEQUENCE public.user_topic_preferences_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_topic_preferences_id_seq OWNER TO the_commons_db_user;

--
-- Name: user_topic_preferences_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: the_commons_db_user
--

ALTER SEQUENCE public.user_topic_preferences_id_seq OWNED BY public.user_topic_preferences.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50),
    email character varying(255) NOT NULL,
    password_hash character varying(255),
    display_name character varying(100),
    bio text,
    role public.userrole,
    algorithm_mode public.algorithmmode,
    is_active boolean,
    is_minor boolean,
    created_at timestamp without time zone,
    last_seen timestamp without time zone
);


ALTER TABLE public.users OWNER TO the_commons_db_user;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: the_commons_db_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO the_commons_db_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: the_commons_db_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: votes; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.votes (
    id integer NOT NULL,
    post_id integer NOT NULL,
    user_id integer NOT NULL,
    value integer NOT NULL
);


ALTER TABLE public.votes OWNER TO the_commons_db_user;

--
-- Name: votes_id_seq; Type: SEQUENCE; Schema: public; Owner: the_commons_db_user
--

CREATE SEQUENCE public.votes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.votes_id_seq OWNER TO the_commons_db_user;

--
-- Name: votes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: the_commons_db_user
--

ALTER SEQUENCE public.votes_id_seq OWNED BY public.votes.id;


--
-- Name: watch_events; Type: TABLE; Schema: public; Owner: the_commons_db_user
--

CREATE TABLE public.watch_events (
    id integer NOT NULL,
    user_id integer NOT NULL,
    post_id integer NOT NULL,
    watch_percent double precision,
    completed boolean,
    recorded_at timestamp without time zone
);


ALTER TABLE public.watch_events OWNER TO the_commons_db_user;

--
-- Name: watch_events_id_seq; Type: SEQUENCE; Schema: public; Owner: the_commons_db_user
--

CREATE SEQUENCE public.watch_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.watch_events_id_seq OWNER TO the_commons_db_user;

--
-- Name: watch_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: the_commons_db_user
--

ALTER SEQUENCE public.watch_events_id_seq OWNED BY public.watch_events.id;


--
-- Name: circle_decisions id; Type: DEFAULT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.circle_decisions ALTER COLUMN id SET DEFAULT nextval('public.circle_decisions_id_seq'::regclass);


--
-- Name: circle_members id; Type: DEFAULT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.circle_members ALTER COLUMN id SET DEFAULT nextval('public.circle_members_id_seq'::regclass);


--
-- Name: community_votes id; Type: DEFAULT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.community_votes ALTER COLUMN id SET DEFAULT nextval('public.community_votes_id_seq'::regclass);


--
-- Name: fingerprint_records id; Type: DEFAULT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.fingerprint_records ALTER COLUMN id SET DEFAULT nextval('public.fingerprint_records_id_seq'::regclass);


--
-- Name: listing_messages id; Type: DEFAULT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.listing_messages ALTER COLUMN id SET DEFAULT nextval('public.listing_messages_id_seq'::regclass);


--
-- Name: listings id; Type: DEFAULT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.listings ALTER COLUMN id SET DEFAULT nextval('public.listings_id_seq'::regclass);


--
-- Name: order_items id; Type: DEFAULT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.order_items ALTER COLUMN id SET DEFAULT nextval('public.order_items_id_seq'::regclass);


--
-- Name: orders id; Type: DEFAULT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.orders ALTER COLUMN id SET DEFAULT nextval('public.orders_id_seq'::regclass);


--
-- Name: posts id; Type: DEFAULT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.posts ALTER COLUMN id SET DEFAULT nextval('public.posts_id_seq'::regclass);


--
-- Name: product_tags id; Type: DEFAULT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.product_tags ALTER COLUMN id SET DEFAULT nextval('public.product_tags_id_seq'::regclass);


--
-- Name: products id; Type: DEFAULT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.products ALTER COLUMN id SET DEFAULT nextval('public.products_id_seq'::regclass);


--
-- Name: seller_profiles id; Type: DEFAULT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.seller_profiles ALTER COLUMN id SET DEFAULT nextval('public.seller_profiles_id_seq'::regclass);


--
-- Name: surplus_donations id; Type: DEFAULT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.surplus_donations ALTER COLUMN id SET DEFAULT nextval('public.surplus_donations_id_seq'::regclass);


--
-- Name: transactions id; Type: DEFAULT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.transactions ALTER COLUMN id SET DEFAULT nextval('public.transactions_id_seq'::regclass);


--
-- Name: user_content_type_preferences id; Type: DEFAULT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.user_content_type_preferences ALTER COLUMN id SET DEFAULT nextval('public.user_content_type_preferences_id_seq'::regclass);


--
-- Name: user_creator_affinity id; Type: DEFAULT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.user_creator_affinity ALTER COLUMN id SET DEFAULT nextval('public.user_creator_affinity_id_seq'::regclass);


--
-- Name: user_topic_preferences id; Type: DEFAULT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.user_topic_preferences ALTER COLUMN id SET DEFAULT nextval('public.user_topic_preferences_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: votes id; Type: DEFAULT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.votes ALTER COLUMN id SET DEFAULT nextval('public.votes_id_seq'::regclass);


--
-- Name: watch_events id; Type: DEFAULT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.watch_events ALTER COLUMN id SET DEFAULT nextval('public.watch_events_id_seq'::regclass);


--
-- Data for Name: circle_decisions; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.circle_decisions (id, subject, decision_type, post_id, outcome, ayes, nays, abstentions, dissent_notes, reasoning, created_at, closed_at) FROM stdin;
\.


--
-- Data for Name: circle_members; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.circle_members (id, user_id, seat_type, region, is_head, elected_at, term_ends, votes_cast) FROM stdin;
\.


--
-- Data for Name: community_votes; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.community_votes (id, post_id, user_id, value, created_at) FROM stdin;
\.


--
-- Data for Name: fingerprint_records; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.fingerprint_records (id, post_id, scan_result, claims_found, deepfake_score, manipulation_score, reviewer, reviewer_notes, decision, decision_reason, scanned_at, decided_at) FROM stdin;
\.


--
-- Data for Name: listing_messages; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.listing_messages (id, listing_id, sender_id, recipient_id, body, is_read, created_at) FROM stdin;
\.


--
-- Data for Name: listings; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.listings (id, title, description, price, media_path, seller_id, is_active, created_at) FROM stdin;
\.


--
-- Data for Name: magic_tokens; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.magic_tokens (token, email, expires) FROM stdin;
35P7xmszwPjHDvz9CQGsPWj2toB9qvAD7pspB2lzQ_c	sentinel.commons@gmail.com	2026-03-23 22:54:42.517227
u9kaQBTkyDAGKidN-8WUBfuj0n8zZthedOtJM-9v8FQ	sentinel.commons@gmail.com	2026-03-23 23:23:41.658145
LGGuXQiw8wuTiIBUVHKk5eLlAAnGfUtamHK4HXQ7R4o	sentinel.commons@gmail.com	2026-03-30 00:27:40.359964
KBkyuuEAjLDVrlcymyWw-lLCrqRjsNfJ7HGYU2xmNak	sentinel.commons@gmail.com	2026-03-27 18:34:00.39114
I_nD-FyB8Z5jE3n5OZkm4SJeko2dD5ZmkUeXsEmvl_M	sentinel.commons@gmail.com	2026-03-28 22:51:50.939838
e8gUp-ivvbR-t2d5imJm53kiOHjfRrP4X2BzHL-ub68	sentinel.commons@gmail.com	2026-03-28 22:51:54.456674
\.


--
-- Data for Name: order_items; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.order_items (id, order_id, product_id, quantity, item_price, line_total) FROM stdin;
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.orders (id, buyer_id, platform_fee, items_total, order_total, status, created_at) FROM stdin;
\.


--
-- Data for Name: posts; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.posts (id, author_id, post_type, content, media_path, status, is_news, is_political, community_score, view_count, created_at, published_at) FROM stdin;
1	1	TEXT	Welcome to The Commons, the first and only social media platform dedicated to wealth redistribution		PUBLISHED	f	f	0	0	2026-03-24 15:55:21.884171	2026-03-24 15:55:21.894821
2	1	TEXT	Welcome to The Commons, the first and only social media platform dedicated to wealth redistribution		PUBLISHED	f	f	0	0	2026-03-24 15:56:08.42497	2026-03-24 15:56:08.433109
3	1	TEXT	Test		PUBLISHED	f	f	0	0	2026-03-25 00:49:50.253125	2026-03-25 00:49:50.264612
\.


--
-- Data for Name: product_tags; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.product_tags (id, post_id, product_id, timestamp_sec) FROM stdin;
\.


--
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.products (id, seller_id, name, description, price, media_path, is_active, community_score, created_at) FROM stdin;
\.


--
-- Data for Name: seller_profiles; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.seller_profiles (id, user_id, business_name, business_type, is_verified, is_corporation, is_publicly_traded, approved_at) FROM stdin;
\.


--
-- Data for Name: surplus_donations; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.surplus_donations (id, period_start, period_end, operating_costs, total_collected, surplus_amount, cause_name, cause_url, cause_description, donated_at, confirmed, public_note, designated_by) FROM stdin;
\.


--
-- Data for Name: transactions; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.transactions (id, buyer_id, product_id, product_price, platform_fee, total, status, created_at) FROM stdin;
\.


--
-- Data for Name: user_content_type_preferences; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.user_content_type_preferences (id, user_id, content_type, score, updated_at) FROM stdin;
\.


--
-- Data for Name: user_creator_affinity; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.user_creator_affinity (id, user_id, creator_id, score, updated_at) FROM stdin;
\.


--
-- Data for Name: user_topic_preferences; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.user_topic_preferences (id, user_id, topic, score, updated_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.users (id, username, email, password_hash, display_name, bio, role, algorithm_mode, is_active, is_minor, created_at, last_seen) FROM stdin;
1	KRONE	sentinel.commons@gmail.com	\N	Krone	Architect of Sentinel, creator of Kinto and Founder of The Commons.	USER	TRANSPARENT	t	f	2026-03-22 22:45:48.440313	2026-03-22 22:45:48.440318
\.


--
-- Data for Name: votes; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.votes (id, post_id, user_id, value) FROM stdin;
\.


--
-- Data for Name: watch_events; Type: TABLE DATA; Schema: public; Owner: the_commons_db_user
--

COPY public.watch_events (id, user_id, post_id, watch_percent, completed, recorded_at) FROM stdin;
\.


--
-- Name: circle_decisions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: the_commons_db_user
--

SELECT pg_catalog.setval('public.circle_decisions_id_seq', 1, false);


--
-- Name: circle_members_id_seq; Type: SEQUENCE SET; Schema: public; Owner: the_commons_db_user
--

SELECT pg_catalog.setval('public.circle_members_id_seq', 1, false);


--
-- Name: community_votes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: the_commons_db_user
--

SELECT pg_catalog.setval('public.community_votes_id_seq', 1, false);


--
-- Name: fingerprint_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: the_commons_db_user
--

SELECT pg_catalog.setval('public.fingerprint_records_id_seq', 1, false);


--
-- Name: listing_messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: the_commons_db_user
--

SELECT pg_catalog.setval('public.listing_messages_id_seq', 1, false);


--
-- Name: listings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: the_commons_db_user
--

SELECT pg_catalog.setval('public.listings_id_seq', 1, false);


--
-- Name: order_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: the_commons_db_user
--

SELECT pg_catalog.setval('public.order_items_id_seq', 1, false);


--
-- Name: orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: the_commons_db_user
--

SELECT pg_catalog.setval('public.orders_id_seq', 1, false);


--
-- Name: posts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: the_commons_db_user
--

SELECT pg_catalog.setval('public.posts_id_seq', 3, true);


--
-- Name: product_tags_id_seq; Type: SEQUENCE SET; Schema: public; Owner: the_commons_db_user
--

SELECT pg_catalog.setval('public.product_tags_id_seq', 1, false);


--
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: the_commons_db_user
--

SELECT pg_catalog.setval('public.products_id_seq', 1, false);


--
-- Name: seller_profiles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: the_commons_db_user
--

SELECT pg_catalog.setval('public.seller_profiles_id_seq', 1, false);


--
-- Name: surplus_donations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: the_commons_db_user
--

SELECT pg_catalog.setval('public.surplus_donations_id_seq', 1, false);


--
-- Name: transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: the_commons_db_user
--

SELECT pg_catalog.setval('public.transactions_id_seq', 1, false);


--
-- Name: user_content_type_preferences_id_seq; Type: SEQUENCE SET; Schema: public; Owner: the_commons_db_user
--

SELECT pg_catalog.setval('public.user_content_type_preferences_id_seq', 1, false);


--
-- Name: user_creator_affinity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: the_commons_db_user
--

SELECT pg_catalog.setval('public.user_creator_affinity_id_seq', 1, false);


--
-- Name: user_topic_preferences_id_seq; Type: SEQUENCE SET; Schema: public; Owner: the_commons_db_user
--

SELECT pg_catalog.setval('public.user_topic_preferences_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: the_commons_db_user
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: votes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: the_commons_db_user
--

SELECT pg_catalog.setval('public.votes_id_seq', 5, true);


--
-- Name: watch_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: the_commons_db_user
--

SELECT pg_catalog.setval('public.watch_events_id_seq', 1, false);


--
-- Name: circle_decisions circle_decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.circle_decisions
    ADD CONSTRAINT circle_decisions_pkey PRIMARY KEY (id);


--
-- Name: circle_members circle_members_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.circle_members
    ADD CONSTRAINT circle_members_pkey PRIMARY KEY (id);


--
-- Name: circle_members circle_members_user_id_key; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.circle_members
    ADD CONSTRAINT circle_members_user_id_key UNIQUE (user_id);


--
-- Name: community_votes community_votes_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.community_votes
    ADD CONSTRAINT community_votes_pkey PRIMARY KEY (id);


--
-- Name: fingerprint_records fingerprint_records_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.fingerprint_records
    ADD CONSTRAINT fingerprint_records_pkey PRIMARY KEY (id);


--
-- Name: fingerprint_records fingerprint_records_post_id_key; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.fingerprint_records
    ADD CONSTRAINT fingerprint_records_post_id_key UNIQUE (post_id);


--
-- Name: listing_messages listing_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.listing_messages
    ADD CONSTRAINT listing_messages_pkey PRIMARY KEY (id);


--
-- Name: listings listings_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.listings
    ADD CONSTRAINT listings_pkey PRIMARY KEY (id);


--
-- Name: magic_tokens magic_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.magic_tokens
    ADD CONSTRAINT magic_tokens_pkey PRIMARY KEY (token);


--
-- Name: votes one_vote_per_post; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.votes
    ADD CONSTRAINT one_vote_per_post UNIQUE (post_id, user_id);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: posts posts_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.posts
    ADD CONSTRAINT posts_pkey PRIMARY KEY (id);


--
-- Name: product_tags product_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.product_tags
    ADD CONSTRAINT product_tags_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: seller_profiles seller_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.seller_profiles
    ADD CONSTRAINT seller_profiles_pkey PRIMARY KEY (id);


--
-- Name: seller_profiles seller_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.seller_profiles
    ADD CONSTRAINT seller_profiles_user_id_key UNIQUE (user_id);


--
-- Name: surplus_donations surplus_donations_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.surplus_donations
    ADD CONSTRAINT surplus_donations_pkey PRIMARY KEY (id);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);


--
-- Name: user_content_type_preferences user_content_type_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.user_content_type_preferences
    ADD CONSTRAINT user_content_type_preferences_pkey PRIMARY KEY (id);


--
-- Name: user_creator_affinity user_creator_affinity_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.user_creator_affinity
    ADD CONSTRAINT user_creator_affinity_pkey PRIMARY KEY (id);


--
-- Name: user_topic_preferences user_topic_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.user_topic_preferences
    ADD CONSTRAINT user_topic_preferences_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: votes votes_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.votes
    ADD CONSTRAINT votes_pkey PRIMARY KEY (id);


--
-- Name: watch_events watch_events_pkey; Type: CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.watch_events
    ADD CONSTRAINT watch_events_pkey PRIMARY KEY (id);


--
-- Name: ix_circle_decisions_id; Type: INDEX; Schema: public; Owner: the_commons_db_user
--

CREATE INDEX ix_circle_decisions_id ON public.circle_decisions USING btree (id);


--
-- Name: ix_circle_members_id; Type: INDEX; Schema: public; Owner: the_commons_db_user
--

CREATE INDEX ix_circle_members_id ON public.circle_members USING btree (id);


--
-- Name: ix_community_votes_id; Type: INDEX; Schema: public; Owner: the_commons_db_user
--

CREATE INDEX ix_community_votes_id ON public.community_votes USING btree (id);


--
-- Name: ix_fingerprint_records_id; Type: INDEX; Schema: public; Owner: the_commons_db_user
--

CREATE INDEX ix_fingerprint_records_id ON public.fingerprint_records USING btree (id);


--
-- Name: ix_order_items_id; Type: INDEX; Schema: public; Owner: the_commons_db_user
--

CREATE INDEX ix_order_items_id ON public.order_items USING btree (id);


--
-- Name: ix_orders_id; Type: INDEX; Schema: public; Owner: the_commons_db_user
--

CREATE INDEX ix_orders_id ON public.orders USING btree (id);


--
-- Name: ix_posts_id; Type: INDEX; Schema: public; Owner: the_commons_db_user
--

CREATE INDEX ix_posts_id ON public.posts USING btree (id);


--
-- Name: ix_product_tags_id; Type: INDEX; Schema: public; Owner: the_commons_db_user
--

CREATE INDEX ix_product_tags_id ON public.product_tags USING btree (id);


--
-- Name: ix_products_id; Type: INDEX; Schema: public; Owner: the_commons_db_user
--

CREATE INDEX ix_products_id ON public.products USING btree (id);


--
-- Name: ix_seller_profiles_id; Type: INDEX; Schema: public; Owner: the_commons_db_user
--

CREATE INDEX ix_seller_profiles_id ON public.seller_profiles USING btree (id);


--
-- Name: ix_surplus_donations_id; Type: INDEX; Schema: public; Owner: the_commons_db_user
--

CREATE INDEX ix_surplus_donations_id ON public.surplus_donations USING btree (id);


--
-- Name: ix_transactions_id; Type: INDEX; Schema: public; Owner: the_commons_db_user
--

CREATE INDEX ix_transactions_id ON public.transactions USING btree (id);


--
-- Name: ix_user_content_type_preferences_id; Type: INDEX; Schema: public; Owner: the_commons_db_user
--

CREATE INDEX ix_user_content_type_preferences_id ON public.user_content_type_preferences USING btree (id);


--
-- Name: ix_user_creator_affinity_id; Type: INDEX; Schema: public; Owner: the_commons_db_user
--

CREATE INDEX ix_user_creator_affinity_id ON public.user_creator_affinity USING btree (id);


--
-- Name: ix_user_topic_preferences_id; Type: INDEX; Schema: public; Owner: the_commons_db_user
--

CREATE INDEX ix_user_topic_preferences_id ON public.user_topic_preferences USING btree (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: the_commons_db_user
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: the_commons_db_user
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: the_commons_db_user
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: ix_watch_events_id; Type: INDEX; Schema: public; Owner: the_commons_db_user
--

CREATE INDEX ix_watch_events_id ON public.watch_events USING btree (id);


--
-- Name: circle_decisions circle_decisions_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.circle_decisions
    ADD CONSTRAINT circle_decisions_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.posts(id);


--
-- Name: circle_members circle_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.circle_members
    ADD CONSTRAINT circle_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: community_votes community_votes_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.community_votes
    ADD CONSTRAINT community_votes_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.posts(id);


--
-- Name: community_votes community_votes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.community_votes
    ADD CONSTRAINT community_votes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: fingerprint_records fingerprint_records_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.fingerprint_records
    ADD CONSTRAINT fingerprint_records_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.posts(id);


--
-- Name: listing_messages listing_messages_listing_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.listing_messages
    ADD CONSTRAINT listing_messages_listing_id_fkey FOREIGN KEY (listing_id) REFERENCES public.listings(id);


--
-- Name: listing_messages listing_messages_recipient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.listing_messages
    ADD CONSTRAINT listing_messages_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES public.users(id);


--
-- Name: listing_messages listing_messages_sender_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.listing_messages
    ADD CONSTRAINT listing_messages_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public.users(id);


--
-- Name: listings listings_seller_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.listings
    ADD CONSTRAINT listings_seller_id_fkey FOREIGN KEY (seller_id) REFERENCES public.users(id);


--
-- Name: order_items order_items_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: order_items order_items_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: orders orders_buyer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_buyer_id_fkey FOREIGN KEY (buyer_id) REFERENCES public.users(id);


--
-- Name: posts posts_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.posts
    ADD CONSTRAINT posts_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.users(id);


--
-- Name: product_tags product_tags_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.product_tags
    ADD CONSTRAINT product_tags_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.posts(id);


--
-- Name: product_tags product_tags_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.product_tags
    ADD CONSTRAINT product_tags_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: products products_seller_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_seller_id_fkey FOREIGN KEY (seller_id) REFERENCES public.seller_profiles(id);


--
-- Name: seller_profiles seller_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.seller_profiles
    ADD CONSTRAINT seller_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: transactions transactions_buyer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_buyer_id_fkey FOREIGN KEY (buyer_id) REFERENCES public.users(id);


--
-- Name: transactions transactions_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: user_content_type_preferences user_content_type_preferences_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.user_content_type_preferences
    ADD CONSTRAINT user_content_type_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_creator_affinity user_creator_affinity_creator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.user_creator_affinity
    ADD CONSTRAINT user_creator_affinity_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES public.users(id);


--
-- Name: user_creator_affinity user_creator_affinity_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.user_creator_affinity
    ADD CONSTRAINT user_creator_affinity_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_topic_preferences user_topic_preferences_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.user_topic_preferences
    ADD CONSTRAINT user_topic_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: votes votes_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.votes
    ADD CONSTRAINT votes_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.posts(id);


--
-- Name: votes votes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.votes
    ADD CONSTRAINT votes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: watch_events watch_events_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.watch_events
    ADD CONSTRAINT watch_events_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.posts(id);


--
-- Name: watch_events watch_events_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: the_commons_db_user
--

ALTER TABLE ONLY public.watch_events
    ADD CONSTRAINT watch_events_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON SEQUENCES TO the_commons_db_user;


--
-- Name: DEFAULT PRIVILEGES FOR TYPES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON TYPES TO the_commons_db_user;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON FUNCTIONS TO the_commons_db_user;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON TABLES TO the_commons_db_user;


--
-- PostgreSQL database dump complete
--

\unrestrict 862w7VtVCieRcGagyHvLHq7tdga2yUozIpDrlAfbBx1vxB6052Vb9jglljoIdbO

