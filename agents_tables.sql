/*
 Navicat PostgreSQL Data Transfer

 Source Server         : Local
 Source Server Type    : PostgreSQL
 Source Server Version : 150015 (150015)
 Source Host           : localhost:5432
 Source Catalog        : testdb
 Source Schema         : public

 Target Server Type    : PostgreSQL
 Target Server Version : 150015 (150015)
 File Encoding         : 65001

 Date: 20/11/2025 11:12:36
*/


-- ----------------------------
-- Table structure for agent_message_metadata
-- ----------------------------
DROP TABLE IF EXISTS "public"."agent_message_metadata";
CREATE TABLE "public"."agent_message_metadata" (
  "id" uuid NOT NULL,
  "message_id" uuid,
  "key" text COLLATE "pg_catalog"."default" NOT NULL,
  "value" text COLLATE "pg_catalog"."default",
  "created_at" timestamptz(6) DEFAULT now()
)
;
ALTER TABLE "public"."agent_message_metadata" OWNER TO "postgres";

-- ----------------------------
-- Table structure for agents
-- ----------------------------
DROP TABLE IF EXISTS "public"."agents";
CREATE TABLE "public"."agents" (
  "id" uuid NOT NULL,
  "agent_name" text COLLATE "pg_catalog"."default" NOT NULL,
  "ip_address" inet,
  "port" int4,
  "created_at" timestamptz(6) DEFAULT now()
)
;
ALTER TABLE "public"."agents" OWNER TO "postgres";

-- ----------------------------
-- Table structure for conversations
-- ----------------------------
DROP TABLE IF EXISTS "public"."conversations";
CREATE TABLE "public"."conversations" (
  "id" uuid NOT NULL,
  "created_at" timestamptz(6) DEFAULT now(),
  "archived" bool NOT NULL,
  "title" text COLLATE "pg_catalog"."default",
  "description" text COLLATE "pg_catalog"."default",
  "metadata" jsonb
)
;
ALTER TABLE "public"."conversations" OWNER TO "postgres";

-- ----------------------------
-- Table structure for message_recipients
-- ----------------------------
DROP TABLE IF EXISTS "public"."message_recipients";
CREATE TABLE "public"."message_recipients" (
  "message_id" uuid NOT NULL,
  "recipient_id" uuid NOT NULL,
  "is_read" bool,
  "read_at" timestamptz(6)
)
;
ALTER TABLE "public"."message_recipients" OWNER TO "postgres";

-- ----------------------------
-- Table structure for messages
-- ----------------------------
DROP TABLE IF EXISTS "public"."messages";
CREATE TABLE "public"."messages" (
  "id" uuid NOT NULL,
  "sender_id" uuid,
  "sent_at" timestamptz(6) DEFAULT now(),
  "parent_message_id" uuid,
  "conversation_id" uuid,
  "content" text COLLATE "pg_catalog"."default" NOT NULL,
  "message_type" text COLLATE "pg_catalog"."default",
  "importance" int4,
  "status" text COLLATE "pg_catalog"."default",
  "metadata" jsonb
)
;
ALTER TABLE "public"."messages" OWNER TO "postgres";

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS "public"."users";
CREATE TABLE "public"."users" (
  "id" int4 NOT NULL DEFAULT nextval('users_id_seq'::regclass),
  "name" varchar(100) COLLATE "pg_catalog"."default" NOT NULL,
  "email" varchar(100) COLLATE "pg_catalog"."default" NOT NULL,
  "created_at" timestamp(6) DEFAULT CURRENT_TIMESTAMP
)
;
ALTER TABLE "public"."users" OWNER TO "postgres";

-- ----------------------------
-- Primary Key structure for table agent_message_metadata
-- ----------------------------
ALTER TABLE "public"."agent_message_metadata" ADD CONSTRAINT "agent_message_metadata_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Primary Key structure for table agents
-- ----------------------------
ALTER TABLE "public"."agents" ADD CONSTRAINT "agents_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Primary Key structure for table conversations
-- ----------------------------
ALTER TABLE "public"."conversations" ADD CONSTRAINT "conversations_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Primary Key structure for table message_recipients
-- ----------------------------
ALTER TABLE "public"."message_recipients" ADD CONSTRAINT "message_recipients_pkey" PRIMARY KEY ("message_id", "recipient_id");

-- ----------------------------
-- Primary Key structure for table messages
-- ----------------------------
ALTER TABLE "public"."messages" ADD CONSTRAINT "messages_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Uniques structure for table users
-- ----------------------------
ALTER TABLE "public"."users" ADD CONSTRAINT "users_email_key" UNIQUE ("email");

-- ----------------------------
-- Primary Key structure for table users
-- ----------------------------
ALTER TABLE "public"."users" ADD CONSTRAINT "users_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Foreign Keys structure for table agent_message_metadata
-- ----------------------------
ALTER TABLE "public"."agent_message_metadata" ADD CONSTRAINT "agent_message_metadata_message_id_fkey" FOREIGN KEY ("message_id") REFERENCES "public"."messages" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table message_recipients
-- ----------------------------
ALTER TABLE "public"."message_recipients" ADD CONSTRAINT "message_recipients_message_id_fkey" FOREIGN KEY ("message_id") REFERENCES "public"."messages" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;
ALTER TABLE "public"."message_recipients" ADD CONSTRAINT "message_recipients_recipient_id_fkey" FOREIGN KEY ("recipient_id") REFERENCES "public"."agents" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table messages
-- ----------------------------
ALTER TABLE "public"."messages" ADD CONSTRAINT "messages_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "public"."conversations" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;
ALTER TABLE "public"."messages" ADD CONSTRAINT "messages_parent_message_id_fkey" FOREIGN KEY ("parent_message_id") REFERENCES "public"."messages" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;
ALTER TABLE "public"."messages" ADD CONSTRAINT "messages_sender_id_fkey" FOREIGN KEY ("sender_id") REFERENCES "public"."agents" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;
