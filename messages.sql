/*
 Navicat PostgreSQL Data Transfer

 Source Server         : Ubuntu25
 Source Server Type    : PostgreSQL
 Source Server Version : 170006 (170006)
 Source Host           : localhost:5432
 Source Catalog        : agentchats
 Source Schema         : messages

 Target Server Type    : PostgreSQL
 Target Server Version : 170006 (170006)
 File Encoding         : 65001

 Date: 12/11/2025 14:07:48
*/


-- ----------------------------
-- Table structure for agent_message_metadata
-- ----------------------------
DROP TABLE IF EXISTS "messages"."agent_message_metadata";
CREATE TABLE "messages"."agent_message_metadata" (
  "id" uuid NOT NULL,
  "message_id" uuid,
  "key" text COLLATE "pg_catalog"."default" NOT NULL,
  "value" text COLLATE "pg_catalog"."default",
  "created_at" timestamp(6) DEFAULT now()
)
;
ALTER TABLE "messages"."agent_message_metadata" OWNER TO "postgres";

-- ----------------------------
-- Table structure for agents
-- ----------------------------
DROP TABLE IF EXISTS "messages"."agents";
CREATE TABLE "messages"."agents" (
  "id" uuid NOT NULL,
  "agent_name" text COLLATE "pg_catalog"."default" NOT NULL,
  "ip_address" inet,
  "port" int4,
  "created_at" timestamp(6) DEFAULT now()
)
;
ALTER TABLE "messages"."agents" OWNER TO "postgres";

-- ----------------------------
-- Table structure for message_recipients
-- ----------------------------
DROP TABLE IF EXISTS "messages"."message_recipients";
CREATE TABLE "messages"."message_recipients" (
  "message_id" uuid NOT NULL,
  "recipient_id" uuid NOT NULL,
  "is_read" bool DEFAULT false,
  "read_at" timestamp(6)
)
;
ALTER TABLE "messages"."message_recipients" OWNER TO "postgres";

-- ----------------------------
-- Table structure for messages
-- ----------------------------
DROP TABLE IF EXISTS "messages"."messages";
CREATE TABLE "messages"."messages" (
  "id" uuid NOT NULL,
  "sender_id" uuid,
  "sent_at" timestamp(6) DEFAULT now(),
  "parent_message_id" uuid,
  "conversation_id" uuid,
  "content" text COLLATE "pg_catalog"."default" NOT NULL,
  "message_type" text COLLATE "pg_catalog"."default",
  "importance" int4,
  "status" text COLLATE "pg_catalog"."default",
  "metadata" jsonb
)
;
ALTER TABLE "messages"."messages" OWNER TO "postgres";

-- ----------------------------
-- Primary Key structure for table agent_message_metadata
-- ----------------------------
ALTER TABLE "messages"."agent_message_metadata" ADD CONSTRAINT "agent_message_metadata_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Primary Key structure for table agents
-- ----------------------------
ALTER TABLE "messages"."agents" ADD CONSTRAINT "agents_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Primary Key structure for table message_recipients
-- ----------------------------
ALTER TABLE "messages"."message_recipients" ADD CONSTRAINT "message_recipients_pkey" PRIMARY KEY ("message_id", "recipient_id");

-- ----------------------------
-- Primary Key structure for table messages
-- ----------------------------
ALTER TABLE "messages"."messages" ADD CONSTRAINT "messages_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Foreign Keys structure for table agent_message_metadata
-- ----------------------------
ALTER TABLE "messages"."agent_message_metadata" ADD CONSTRAINT "agent_message_metadata_message_id_fkey" FOREIGN KEY ("message_id") REFERENCES "messages"."messages" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table message_recipients
-- ----------------------------
ALTER TABLE "messages"."message_recipients" ADD CONSTRAINT "message_recipients_message_id_fkey" FOREIGN KEY ("message_id") REFERENCES "messages"."messages" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;
ALTER TABLE "messages"."message_recipients" ADD CONSTRAINT "message_recipients_recipient_id_fkey" FOREIGN KEY ("recipient_id") REFERENCES "messages"."agents" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table messages
-- ----------------------------
ALTER TABLE "messages"."messages" ADD CONSTRAINT "messages_parent_message_id_fkey" FOREIGN KEY ("parent_message_id") REFERENCES "messages"."messages" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;
ALTER TABLE "messages"."messages" ADD CONSTRAINT "messages_sender_id_fkey" FOREIGN KEY ("sender_id") REFERENCES "messages"."agents" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;
