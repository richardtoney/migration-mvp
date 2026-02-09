package com.example.entity;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.Table;
import org.hibernate.annotations.Type;
import org.hibernate.annotations.TypeDef;
import org.hibernate.annotations.TypeDefs;
import com.vladmihalcea.hibernate.type.json.JsonType;

import java.util.Map;
import java.util.UUID;

@TypeDefs({
    @TypeDef(name = "json", typeClass = JsonType.class)
})
@Entity
@Table(name = "products")
public class Product {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Type(type = "uuid-char")
    @Column(name = "external_id", length = 36)
    private UUID externalId;

    @Type(type = "json")
    @Column(name = "metadata", columnDefinition = "json")
    private Map<String, Object> metadata;

    @Type(type = "yes_no")
    @Column(name = "active")
    private Boolean active;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public UUID getExternalId() { return externalId; }
    public void setExternalId(UUID externalId) { this.externalId = externalId; }

    public Map<String, Object> getMetadata() { return metadata; }
    public void setMetadata(Map<String, Object> metadata) { this.metadata = metadata; }

    public Boolean getActive() { return active; }
    public void setActive(Boolean active) { this.active = active; }
}
