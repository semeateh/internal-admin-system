USE internal_admin_system;

ALTER TABLE flow_instances
  ADD COLUMN cloud_path VARCHAR(500) DEFAULT NULL COMMENT 'Shared drive path' AFTER instance_name;
